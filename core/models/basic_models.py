from dataclasses import dataclass
from typing import Any, Optional, List
@dataclass
class ContractSuccessCalcResult:
    wis_roll: Any
    cha_roll: Any
    int_roll: Any
    xp_gained: int
    gold_gained: int
    loot_tier: str
@dataclass
class CorruptionResult:
    roll: Any
    is_fail: bool
    damage: int
    new_diseases: List[str]

@dataclass
class RitualResult:
    roll: Any
    is_success: bool
    new_buff: Optional[str]


@dataclass
class ContractCompleteResult:
    xp_gained: int
    gold_gained: int
    items_found: List[str]
    wis_roll: Any
    cha_roll: Any
    int_roll: Any


@dataclass
class ContractFailResult:
    hp_lost: int
    is_crit_fail: bool
    new_injuries: List[str]
    dex_roll: Any


@dataclass
class PurchaseResult:
    success: bool
    error: Optional[str] = None
    item_name: Optional[str] = None
    spent: int = 0