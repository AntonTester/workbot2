import random
from typing import List
from core.models.quest_models import Quest, TaskStep, Action, QuestCheckResult, QuestBuyResult
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
        """
        Выполняет проверку навыка.
        Тратит энергию, рассчитывает бросок через GameCalculator, начисляет флаги и награды.
        """
        if not self.quest or self.quest.status != "active":
            return QuestCheckResult(False, "Квест не найден или завершен.", None, 0, False)

        # Находим нужную задачу и проверку
        task = next((t for t in self.quest.task_steps if t.name == task_name), None)
        if not task or check_index >= len(task.checks):
            return QuestCheckResult(False, "Задача или проверка не найдена.", None, 0, False)

        check = task.checks[check_index]

        # 1. Проверка Энергии
        if self.hero_ctrl.model.energy < check.energy:
            return QuestCheckResult(False, "Недостаточно энергии! Герой истощен.", None, 0, False)

        self.hero_ctrl.model.energy -= check.energy

        # 2. Сбор экстра-бонусов от усилителей (Boosts)
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

        # 3. Бросок кубика через Калькулятор
        dc = int(check.difficulty)
        roll_data = GameCalculator.calculate_quest_check(
            self.hero_ctrl.model,
            self.hero_ctrl.active_statuses,
            check.skill,
            dc,
            extra_bonus
        )

        quest_completed = False
        gold_gained = 0
        xp_gained = 0

        # 4. Обработка результатов
        if roll_data.is_success:
            # Выдаем флаги
            for f in check.success_effect:
                if f not in self.quest.flags:
                    self.quest.flags.append(f)

            # Проверяем условие победы в Квесте
            if "win" in self.quest.flags:
                self.quest.status = "completed"
                gold_gained = self.quest.gold_reward
                xp_gained = self.quest.exp_reward

                self.hero_ctrl._add_gold(gold_gained)
                self.hero_ctrl._add_xp(xp_gained)
                quest_completed = True
                message = check.success_message
            else:
                message = check.success_message
        else:
            message = check.fail_message

        # 5. Сохранение состояния
        self.repo.save_quest(self.hero_ctrl.model.user_id, self.quest)
        await self.hero_ctrl.save_all()  # Сохраняем энергию, золото и ХП

        return QuestCheckResult(
            success=roll_data.is_success,
            message=message,
            roll_data=roll_data,
            energy_spent=check.energy,
            quest_completed=quest_completed,
            gold_reward=gold_gained,
            xp_reward=xp_gained
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