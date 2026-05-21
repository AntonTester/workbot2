class RollData:
    def __init__(self, roll_type, stat_name, dc, pure_roll, total, is_crit_success, is_crit_fail, advantage,
                 disadvantage, bonuses, dice_rolls=None):
        self.roll_type = roll_type
        self.stat_name = stat_name
        self.dc = dc
        self.pure_roll = pure_roll
        self.total = total
        self.is_crit_success = is_crit_success
        self.is_crit_fail = is_crit_fail
        self.advantage = advantage
        self.disadvantage = disadvantage
        self.bonuses = bonuses

        # Сохраняем массив выпавших кубиков
        self.dice_rolls = dice_rolls or [pure_roll]

        # Авторасчет успеха
        self.is_success = total >= dc if not is_crit_fail else False
        if is_crit_success: self.is_success = True