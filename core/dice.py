import random

class Dice:
    @staticmethod
    def roll(advantage: bool = False, disadvantage: bool = False) -> dict:
        r1 = random.randint(1, 20)
        r2 = random.randint(1, 20)
        rolls = [r1]

        # Если есть и преимущество, и помеха - они отменяют друг друга
        if advantage and not disadvantage:
            rolls = [r1, r2]
            pure_roll = max(r1, r2)
        elif disadvantage and not advantage:
            rolls = [r1, r2]
            pure_roll = min(r1, r2)
        else:
            pure_roll = r1

        return {
            "pure_roll": pure_roll,
            "rolls": rolls,  # <--- Добавили сохранение всех бросков
            "is_crit_success": pure_roll == 20,
            "is_crit_fail": pure_roll == 1
        }