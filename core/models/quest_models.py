from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class Action:
    name: str
    display_name: str
    price: int
    effect: str

@dataclass
class CycleStep:
    number: int
    display_name: str
    description: str

@dataclass
class Boost:
    flags_check: str
    bonus: str
    skills: List[str]
    is_disposable: bool

@dataclass
class Check:
    skill: str
    display_name: str
    difficulty: str
    energy: int
    success_message: str
    fail_message: str
    success_effect: List[str]

@dataclass
class TaskStep:
    name: str
    display_name: str
    description: str
    flags_dependency: List[str]
    flags_block: List[str]
    boost: List[Boost]
    checks: List[Check]

@dataclass
class Quest:
    quest_name: str
    description: str
    gold_reward: int
    exp_reward: int
    max_days: int
    skills: List[str]
    actions: List[Action]
    cycle_steps: List[CycleStep]
    task_steps: List[TaskStep]
    flags: List[str] = field(default_factory=list)
    current_day: int = 0
    status: str = "active" # active, completed, failed

@dataclass
class QuestCheckResult:
    """Типизированный результат выполнения проверки в квесте."""
    success: bool
    message: str
    roll_data: Any  # Объект броска кубика (RollData) для форматирования в texts.py
    energy_spent: int
    quest_completed: bool
    gold_reward: int = 0
    xp_reward: int = 0

@dataclass
class QuestBuyResult:
    """Типизированный результат покупки экшена в квесте."""
    success: bool
    message: str