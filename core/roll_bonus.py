from dataclasses import dataclass

@dataclass
class RollBonus:
    """Хранит информацию о конкретном слагаемом в броске (бонусе или штрафе)."""
    value: int
    source: str