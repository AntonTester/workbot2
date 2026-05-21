from enum import Enum


# === 1. Флаги ===
class StatusFlag(Enum):
    STACKABLE = "STACKABLE"
    IS_INJURE = "IS_INJURE"


# === 2. Базовые классы ===
class StatusTemplate:
    """Базовый класс для всех состояний."""

    type = "unknown"

    def __init__(self, unique_name: str, name_text: str, description: str, effect_desc: str, flags: list = None,
                 effects: dict = None):
        self.unique_name = unique_name
        self.name_text = name_text
        self.description = description
        self.effect = effect_desc
        self.flags = flags if flags else []
        self.effects = effects if effects else {}


class Buff(StatusTemplate):
    type = "buff"

    def __init__(self, unique_name: str, name_text: str, description: str, effect_desc: str, flags: list = None,
                 effects: dict = None):
        super().__init__(unique_name, name_text, description, effect_desc, flags, effects)


class Injury(StatusTemplate):
    type = "injury"

    def __init__(self, unique_name: str, name_text: str, description: str, effect_desc: str, flags: list = None,
                 effects: dict = None):
        _flags = flags if flags else []
        # Сохраняем флаг как строку для совместимости с БД
        if "IS_INJURE" not in _flags and StatusFlag.IS_INJURE.value not in _flags:
            _flags.append(StatusFlag.IS_INJURE.value)
        super().__init__(unique_name, name_text, description, effect_desc, _flags, effects)


class Disease(StatusTemplate):
    type = "disease"

    def __init__(self, unique_name: str, name_text: str, description: str, effect_desc: str, duration_days: int,
                 flags: list = None, effects: dict = None):
        super().__init__(unique_name, name_text, description, effect_desc, flags, effects)
        self.duration_days = duration_days

class Debuff:
    """Временный негативный эффект (чаще всего от квестов)."""
    type = 'debuff'
    def __init__(self, name: str, name_text: str, description: str, effect: str, duration_days: int, flags: list, effects: dict):
        self.name = name
        self.name_text = name_text
        self.description = description
        self.effect = effect
        self.duration_days = duration_days
        self.flags = flags
        self.effects = effects

# === 3. Реестр (База данных игры в памяти) ===
class StatusRegistry:
    """Хранилище всех доступных в игре состояний."""
    _statuses = {}

    @classmethod
    def load(cls, templates_dict: dict):
        cls._statuses = templates_dict

    @classmethod
    def get(cls, unique_name: str) -> StatusTemplate:
        return cls._statuses.get(unique_name)

    @classmethod
    def get_all_buffs(cls) -> list[str]:
        return [k for k, v in cls._statuses.items() if isinstance(v, Buff)]

    @classmethod
    def get_all_injuries(cls) -> list[str]:
        return [k for k, v in cls._statuses.items() if isinstance(v, Injury)]

    @classmethod
    def get_all_diseases(cls) -> list[str]:
        return [k for k, v in cls._statuses.items() if isinstance(v, Disease)]