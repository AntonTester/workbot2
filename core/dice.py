import random


class Dice:
    """Виртуальный d20 кубик с механикой критов, преимущества и помехи."""

    @staticmethod
    def roll(advantage: bool = False, disadvantage: bool = False) -> dict:
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)

        if advantage and not disadvantage:
            base_roll = max(roll1, roll2)
        elif disadvantage and not advantage:
            base_roll = min(roll1, roll2)
        else:
            base_roll = roll1

        return {
            "pure_roll": base_roll,
            "is_crit_success": base_roll == 20,
            "is_crit_fail": base_roll == 1
        }