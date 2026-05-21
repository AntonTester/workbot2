from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class Action:
    name: str
    display_name: str
    price: int
    effect: str

@dataclass
class TaskEffect:
    """Эффект, применяемый при успехе или провале (flag, damage, debuff)."""
    type_effect: str
    value: str

@dataclass
class Check:
    """Проверка навыка без энергии, но с массивами эффектов."""
    skill: str
    display_name: str
    difficulty: str
    success_message: str
    fail_message: str
    success_effects: List[TaskEffect] = field(default_factory=list)
    fail_effects: List[TaskEffect] = field(default_factory=list)

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
class TaskEffect:
    """Эффект, применяемый при успехе или провале (flag, damage, debuff)."""
    type_effect: str
    value: str

@dataclass
class Check:
    """Проверка навыка без энергии, но с массивами эффектов."""
    skill: str
    display_name: str
    difficulty: str
    success_message: str
    fail_message: str
    success_effects: List[TaskEffect] = field(default_factory=list)
    fail_effects: List[TaskEffect] = field(default_factory=list)


@dataclass
class QuestCheckResult:
    """Типизированный результат выполнения проверки в квесте."""
    success: bool
    message: str
    roll_data: Any
    quest_completed: bool
    gold_reward: int = 0
    xp_reward: int = 0
    damage_taken: int = 0                     # <--- НОВОЕ ПОЛЕ
    debuffs_received: List[str] = field(default_factory=list) # <--- НОВОЕ ПОЛЕ

@dataclass
class QuestBuyResult:
    success: bool
    message: str

@dataclass
class QuestEventResult:
    """Результат продвижения квеста на следующий день."""
    success: bool
    message: str
    is_failed: bool = False
    step_title: str = ""
    step_desc: str = ""
    day: int = 0

