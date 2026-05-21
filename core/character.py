class Character:
    # Привязка навыков к статам D&D
    SKILL_MAP = {
        "Атлетика": "STR", "Акробатика": "DEX", "Ловкость рук": "DEX", "Скрытность": "DEX",
        "Магия": "INT", "История": "INT", "Расследование": "INT", "Природа": "INT", "Религия": "INT",
        "Уход за животными": "WIS", "Проницательность": "WIS", "Медицина": "WIS", "Восприятие": "WIS", "Выживание": "WIS",
        "Обман": "CHA", "Запугивание": "CHA", "Выступление": "CHA", "Убеждение": "CHA"
    }

    def __init__(self, user_id: int, name: str = "Астра Лисмор"):
        self.user_id = user_id
        self.name = name
        self.hp = 9
        self.max_hp = 9
        self.xp = 0
        self.level = 1
        self.gold = 0
        self.stats = {
            "STR": 8, "DEX": 14, "CON": 12,
            "INT": 14, "WIS": 16, "CHA": 12
        }

    def get_skill_bonus(self, skill_name: str) -> int:
        """Считает бонус навыка: 2 + модификатор характеристики."""
        stat_key = self.SKILL_MAP.get(skill_name, "STR")
        stat_val = self.stats.get(stat_key, 10)
        modifier = (stat_val - 10) // 2
        return 2 + modifier