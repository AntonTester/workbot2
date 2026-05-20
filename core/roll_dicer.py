from core.dice import Dice
from core.roll_bonus import RollBonus
from core.roll_data import RollData
from core.status_registry import StatusRegistry


class RollDicer:
    """Движок для проведения любых проверок и спасбросков."""

    @staticmethod
    def roll(
            character_model,
            active_statuses: list,
            stat_key: str,
            dc: int,
            roll_type: str = "Проверка",
            advantage: bool = False,
            disadvantage: bool = False,
            extra_bonuses: list[RollBonus] = None  # <--- ДОБАВЛЕН ПАРАМЕТР
    ) -> RollData:

        # 1. Бросаем физический кубик
        dice_result = Dice.roll(advantage, disadvantage)
        pure_roll = dice_result["pure_roll"]

        bonuses = []
        bonuses.append(RollBonus(value=pure_roll, source="Бросок d20"))

        # 2. Высчитываем итоговую характеристику с учетом эффектов статусов
        base_val = character_model.stats.get(stat_key, 10)
        stat_effect_sum = 0
        roll_bonus_sum = 0

        for s in active_statuses:
            # Поддержка словарей (старая БД) и объектов (новая архитектура)
            name_key = s.name if hasattr(s, 'name') else s["name"]
            template = StatusRegistry.get(name_key)

            if template and hasattr(template, 'effects'):
                # Влияние на саму характеристику (например, -2 к Силе от травмы)
                stat_effect_sum += template.effects.get(stat_key, 0)

                # Прямые бонусы/штрафы к самому броску
                b1 = template.effects.get(f"ROLL_BONUS_{stat_key}", 0)
                b2 = template.effects.get("ROLL_BONUS", 0)
                if b1 + b2 != 0:
                    bonuses.append(RollBonus(value=b1 + b2, source=template.name_text))
                    roll_bonus_sum += (b1 + b2)

        # Обрабатываем новые дополнительные бонусы (от навыков и квестов)
        if extra_bonuses:
            for extra_b in extra_bonuses:
                bonuses.append(extra_b)
                roll_bonus_sum += extra_b.value

        final_stat = max(1, base_val + stat_effect_sum)
        stat_mod = (final_stat - 10) // 2

        if stat_mod != 0:
            bonuses.append(RollBonus(value=stat_mod, source=f"Модификатор {stat_key}"))

        # 3. Подбиваем итог
        total = pure_roll + stat_mod + roll_bonus_sum

        # 4. Формируем и возвращаем объект с данными
        return RollData(
            roll_type=roll_type,
            stat_name=stat_key,
            dc=dc,
            pure_roll=pure_roll,
            total=total,
            is_crit_success=dice_result["is_crit_success"],
            is_crit_fail=dice_result["is_crit_fail"],
            advantage=advantage,
            disadvantage=disadvantage,
            bonuses=bonuses
        )