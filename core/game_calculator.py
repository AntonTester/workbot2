from typing import Any

from core.models.basic_models import ContractSuccessCalcResult
from core.roll_dicer import RollDicer


class GameCalculator:
    RITUAL_DC = 13
    CORRUPTION_DC = 12
    WIS_CONTRACT_DC = 12
    CHA_CONTRACT_DC = 15
    INT_CONTRACT_DC = 13
    FAIL_CONTRACT_DC = 14

    XP_TABLE = {
        1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
        6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
        11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
        16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
    }

    # Карта навыков (поддерживает и английские, и русские ключи из JSON)
    SKILL_MAP = {
        "athletics": ("Атлетика", "STR"), "атлетика": ("Атлетика", "STR"),
        "acrobatics": ("Акробатика", "DEX"), "акробатика": ("Акробатика", "DEX"),
        "sleight_of_hand": ("Ловкость рук", "DEX"), "ловкость рук": ("Ловкость рук", "DEX"),
        "stealth": ("Скрытность", "DEX"), "скрытность": ("Скрытность", "DEX"),
        "arcana": ("Магия", "INT"), "магия": ("Магия", "INT"),
        "history": ("История", "INT"), "история": ("История", "INT"),
        "investigation": ("Расследование", "INT"), "расследование": ("Расследование", "INT"),
        "nature": ("Природа", "INT"), "природа": ("Природа", "INT"),
        "religion": ("Религия", "INT"), "религия": ("Религия", "INT"),
        "animal_handling": ("Уход за животными", "WIS"), "уход за животными": ("Уход за животными", "WIS"),
        "insight": ("Проницательность", "WIS"), "проницательность": ("Проницательность", "WIS"),
        "medicine": ("Медицина", "WIS"), "медицина": ("Медицина", "WIS"),
        "perception": ("Восприятие", "WIS"), "восприятие": ("Восприятие", "WIS"),
        "survival": ("Выживание", "WIS"), "выживание": ("Выживание", "WIS"),
        "deception": ("Обман", "CHA"), "обман": ("Обман", "CHA"),
        "intimidation": ("Запугивание", "CHA"), "запугивание": ("Запугивание", "CHA"),
        "performance": ("Выступление", "CHA"), "выступление": ("Выступление", "CHA"),
        "persuasion": ("Убеждение", "CHA"), "убеждение": ("Убеждение", "CHA")
    }

    # Профильные навыки Астры (получают +2)
    ASTRA_PROFICIENCIES = ["Убеждение", "Восприятие", "Проницательность", "Атлетика", "Природа", "История"]

    @classmethod
    def calculate_quest_check(cls, model, active_statuses, raw_skill_name: str, dc: int, extra_bonus_val: int) -> Any:
        """
        Рассчитывает бросок навыка через стандартный RollDicer.
        Бонус мастерства (+2) дается ТОЛЬКО если навык есть в ASTRA_PROFICIENCIES.
        """
        from core.roll_dicer import RollDicer
        from core.roll_bonus import RollBonus

        # Переводим навык на русский и определяем стату (например: "Убеждение", "CHA")
        skill_key_lower = raw_skill_name.lower().strip()
        skill_name_ru, stat_key = cls.SKILL_MAP.get(skill_key_lower, (raw_skill_name, "STR"))

        extra_bonuses = []

        # Проверка на владение навыком (Proficiency)
        if skill_name_ru in cls.ASTRA_PROFICIENCIES:
            extra_bonuses.append(RollBonus(value=2, source="Мастерство"))

        # Добавляем бонусы от предметов/экшенов квеста
        if extra_bonus_val > 0:
            extra_bonuses.append(RollBonus(value=extra_bonus_val, source="Усилитель (Boost)"))

        # Вызываем честный движок бросков!
        roll_data = RollDicer.roll(
            character_model=model,
            active_statuses=active_statuses,
            stat_key=stat_key,
            dc=dc,
            roll_type=f"Проверка: {skill_name_ru}",
            advantage=False,
            disadvantage=False,
            extra_bonuses=extra_bonuses
        )

        return roll_data
    @classmethod
    def calculate_purchase(cls, current_gold: int, item_price: int) -> tuple[bool, int]:
        if current_gold >= item_price:
            return True, item_price
        return False, 0

    @classmethod
    def calculate_ritual(cls, model, active_statuses, adv: bool, disadv: bool) -> tuple[Any, bool]:
        roll = RollDicer.roll(model, active_statuses, "STR", cls.RITUAL_DC, "Ритуал (Проверка Силы)", adv, disadv)
        return roll, roll.is_success

    @classmethod
    def calculate_corruption(cls, model, active_statuses, adv: bool, disadv: bool) -> tuple[Any, int, int]:
        roll = RollDicer.roll(model, active_statuses, "CON", cls.CORRUPTION_DC, "Скверна (Спасбросок Выносливости)",
                              adv, disadv)

        if not roll.is_success:
            count = 2 if roll.is_crit_fail else 1
            damage = 10 if roll.is_crit_fail else 5
            return roll, damage, count
        return roll, 5, 0

    @classmethod
    def calculate_contract_success(cls, model, active_statuses, difficulty: str, duration: str, flags_adv: dict,
                                   flags_disadv: dict) -> ContractSuccessCalcResult:
        gold_map = {"Легкий": 5, "Средний": 15, "Сложный": 25, "Невероятный": 50}
        xp_map = {"До 15 минут": 10, "До 2 часов": 30, "До дня": 80}

        base_gold = gold_map.get(difficulty, 10)
        base_xp = xp_map.get(duration, 100)

        wis_roll = RollDicer.roll(model, active_statuses, "WIS", cls.WIS_CONTRACT_DC, "Проверка Мудрости (Опыт)",
                                  flags_adv.get("WIS", False), flags_disadv.get("WIS", False))
        cha_roll = RollDicer.roll(model, active_statuses, "CHA", cls.CHA_CONTRACT_DC, "Проверка Харизмы (Золото)",
                                  flags_adv.get("CHA", False), flags_disadv.get("CHA", False))
        int_roll = RollDicer.roll(model, active_statuses, "INT", cls.INT_CONTRACT_DC, "Проверка Интеллекта (Лут)",
                                  flags_adv.get("INT", False), flags_disadv.get("INT", False))

        final_xp = base_xp + int(base_xp * 0.2) if wis_roll.is_success else base_xp
        final_gold = base_gold

        total_int = int_roll.total
        if total_int >= 21:
            loot_tier = "precious"
        elif total_int >= 17:
            loot_tier = "component"
        elif total_int >= 13:
            loot_tier = "potion"
        else:
            loot_tier = "junk"

        return ContractSuccessCalcResult(
            wis_roll=wis_roll,
            cha_roll=cha_roll,
            int_roll=int_roll,
            xp_gained=final_xp,
            gold_gained=final_gold,
            loot_tier=loot_tier
        )

    @classmethod
    def calculate_contract_fail(cls, model, active_statuses, adv: bool, disadv: bool) -> tuple[Any, int, int]:
        roll = RollDicer.roll(model, active_statuses, "DEX", cls.FAIL_CONTRACT_DC, "Спасбросок Ловкости (Провал)", adv,
                              disadv)

        hp_loss = 20 if roll.is_crit_fail else 10
        injuries_count = 0

        if not roll.is_success:
            injuries_count = 2 if roll.is_crit_fail else 1

        return roll, hp_loss, injuries_count

    @classmethod
    def calculate_stat_modifier(cls, base_val: int, effect_sum: int) -> tuple[int, int]:
        final_val = max(1, base_val + effect_sum)
        modifier = (final_val - 10) // 2
        return final_val, modifier

    @classmethod
    def check_level_up(cls, current_level: int, current_xp: int) -> tuple[int, bool]:
        new_level = current_level
        leveled_up = False

        while new_level < 20:
            next_level_xp = cls.XP_TABLE.get(new_level + 1, float('inf'))
            if current_xp >= next_level_xp:
                new_level += 1
                leveled_up = True
            else:
                break
        return new_level, leveled_up