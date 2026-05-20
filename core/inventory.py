class Inventory:
    """Хранение лута и зелий (в памяти для механик)."""

    def __init__(self, character):
        self.character = character
        self.items = {}

    def add_item(self, item_name: str, quantity: int = 1):
        self.items[item_name] = self.items.get(item_name, 0) + quantity

    def use_potion(self, potion_name: str, status_manager=None):
        if self.items.get(potion_name, 0) > 0:
            self.items[potion_name] -= 1
            if potion_name == "Зелье Лечения":
                multiplier = 0.5 if status_manager and status_manager.has_status("Некротическая Кара") else 1.0
                self.character.heal(int(50 * multiplier))
            return True
        return False