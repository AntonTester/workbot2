from dataclasses import dataclass, field
from core.roll_bonus import RollBonus

@dataclass
class RollData:
    """Полный отчет о совершенном броске кубика."""
    roll_type: str       # "Проверка" или "Спасбросок"
    stat_name: str       # "STR", "CON", "INT" и т.д.
    dc: int              # Сложность (Difficulty Class)
    pure_roll: int       # Чистое значение кубика (1-20)
    total: int           # Итоговый результат со всеми модификаторами
    is_crit_success: bool
    is_crit_fail: bool
    advantage: bool = False
    disadvantage: bool = False
    bonuses: list[RollBonus] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """Автоматически определяет, пройден ли бросок, учитывая криты и сложность."""
        if self.is_crit_success:
            return True
        if self.is_crit_fail:
            return False
        return self.total >= self.dc