import random
from typing import List
from core.models.quest_models import Quest, TaskStep, Action, QuestCheckResult, QuestBuyResult, QuestEventResult
from core.game_calculator import GameCalculator
from db.quest_repo import QuestRepo


class QuestController:
    """
    Управленец состоянием Квестов.
    Делегирует математику бросков в GameCalculator, а сохранение — в QuestRepo.
    """

    def __init__(self, character_controller, quest_repo: QuestRepo):
        self.hero_ctrl = character_controller
        self.repo = quest_repo
        self.quest = self.repo.get_active_quest(self.hero_ctrl.model.user_id)

    def process_daily_event(self) -> QuestEventResult:
        """Перематывает день вперед и возвращает текстовый эвент."""
        if not self.quest or self.quest.status != "active":
            return QuestEventResult(False, "Нет активного квеста.")

        self.quest.current_day += 1

        # Если закончились лимиты дней (эвенты)
        if self.quest.current_day >= len(self.quest.cycle_steps):
            self.quest.status = "failed"
            self.repo.save_quest(self.hero_ctrl.model.user_id, self.quest)
            return QuestEventResult(True, "Время вышло", is_failed=True)

        # Достаем эвент текущего дня и сохраняем прогресс!
        current_step = self.quest.cycle_steps[self.quest.current_day]
        self.repo.save_quest(self.hero_ctrl.model.user_id, self.quest)

        return QuestEventResult(
            success=True,
            message="Успех",
            step_title=current_step.display_name,
            step_desc=current_step.description,
            day=self.quest.current_day
        )

    def get_available_tasks(self) -> List[TaskStep]:
        """Возвращает задачи, у которых выполнены зависимости и нет блокирующих флагов."""
        if not self.quest or self.quest.status != "active":
            return []

        available = []
        q_flags = set(self.quest.flags)

        for task in self.quest.task_steps:
            # Проверяем наличие всех требуемых флагов
            deps_met = all(f in q_flags for f in task.flags_dependency) if task.flags_dependency else True
            # Проверяем отсутствие блокирующих флагов
            not_blocked = not any(f in q_flags for f in task.flags_block) if task.flags_block else True

            if deps_met and not_blocked:
                available.append(task)

        return available

    async def perform_task_check(self, task_name: str, check_index: int) -> QuestCheckResult:
        """Выполняет проверку навыка, применяет TaskEffects и начисляет награды."""
        if not self.quest or self.quest.status != "active":
            return QuestCheckResult(False, "Квест не найден или завершен.", None, False)

        task = next((t for t in self.quest.task_steps if t.name == task_name), None)
        if not task or check_index >= len(task.checks):
            return QuestCheckResult(False, "Задача или проверка не найдена.", None, False)

        check = task.checks[check_index]

        # 1. Сбор экстра-бонусов от усилителей (Boosts)
        extra_bonus = 0
        used_disposable_flags = []

        for boost in task.boost:
            if boost.flags_check in self.quest.flags and check.skill in boost.skills:
                if 'd' in boost.bonus:
                    sides = int(boost.bonus.split('d')[1])
                    extra_bonus += random.randint(1, sides)
                else:
                    extra_bonus += int(boost.bonus)

                if boost.is_disposable:
                    used_disposable_flags.append(boost.flags_check)

        # Удаляем одноразовые флаги
        for f in used_disposable_flags:
            self.quest.flags.remove(f)

        # 2. Бросок кубика через Калькулятор
        dc = int(check.difficulty)
        roll_data = GameCalculator.calculate_quest_check(
            self.hero_ctrl.model,
            self.hero_ctrl.active_statuses,
            check.skill,
            dc,
            extra_bonus
        )

        # 3. Обработка динамических эффектов (TaskEffects)
        effects_to_apply = check.success_effects if roll_data.is_success else check.fail_effects

        damage_taken = 0
        debuffs_received = []

        for eff in effects_to_apply:
            if eff.type_effect == "flag":
                if eff.value not in self.quest.flags:
                    self.quest.flags.append(eff.value)

            elif eff.type_effect == "damage":
                dmg = 0
                val = eff.value.lower()
                if 'd' in val:
                    parts = val.split('d')
                    count = int(parts[0]) if parts[0] else 1
                    sides = int(parts[1])
                    for _ in range(count):
                        dmg += random.randint(1, sides)
                else:
                    dmg = int(val)
                damage_taken += dmg

            elif eff.type_effect == "debuff":
                print("ga")
                self.hero_ctrl._apply_status(eff.value)
                debuffs_received.append(eff.value)

        # Применяем полученный урон
        if damage_taken > 0:
            self.hero_ctrl._modify_hp(-damage_taken)

        # 4. Проверяем условие победы в Квесте
        quest_completed = False
        gold_gained = 0
        xp_gained = 0

        if "win" in self.quest.flags:
            self.quest.status = "completed"
            gold_gained = self.quest.gold_reward
            xp_gained = self.quest.exp_reward
            self.hero_ctrl._add_gold(gold_gained)
            self.hero_ctrl._add_xp(xp_gained)
            quest_completed = True

        message = check.success_message if roll_data.is_success else check.fail_message

        # 5. Сохранение состояния
        self.repo.save_quest(self.hero_ctrl.model.user_id, self.quest)
        await self.hero_ctrl.save_all()

        return QuestCheckResult(
            success=roll_data.is_success,
            message=message,
            roll_data=roll_data,
            quest_completed=quest_completed,
            gold_reward=gold_gained,
            xp_reward=xp_gained,
            damage_taken=damage_taken,
            debuffs_received=debuffs_received
        )

    async def buy_action(self, action_name: str) -> QuestBuyResult:
        """Покупка экшена/усилителя за золото."""
        if not self.quest or self.quest.status != "active":
            return QuestBuyResult(False, "Нет активного квеста.")

        action = next((a for a in self.quest.actions if a.name == action_name), None)
        if not action:
            return QuestBuyResult(False, "Действие не найдено.")

        if self.hero_ctrl.model.gold < action.price:
            return QuestBuyResult(False, "Недостаточно золота.")

        # Списываем золото через контроллер персонажа
        self.hero_ctrl._add_gold(-action.price)

        if action.effect not in self.quest.flags:
            self.quest.flags.append(action.effect)

        self.repo.save_quest(self.hero_ctrl.model.user_id, self.quest)
        await self.hero_ctrl.save_all()

        return QuestBuyResult(True, f"Куплено: {action.display_name}!")