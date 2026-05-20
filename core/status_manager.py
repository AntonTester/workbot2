class StatusManager:
    """Управление реестром состояний через базу данных."""

    def __init__(self, character, status_repo):
        self.character = character
        self.repo = status_repo
        self.active_statuses = self.repo.load_active_statuses(self.character.user_id)

    def add_status(self, name: str, status_type: str, duration_hours: int = None):
        if status_type in ["injury", "disease"] and self.has_status("Эгида"):
            self.remove_status("Эгида")
            return False

        self.repo.add_status(self.character.user_id, name, status_type, duration_hours)
        self.active_statuses = self.repo.load_active_statuses(self.character.user_id)
        self._apply_immediate_effects(name)
        return True

    def has_status(self, name: str) -> bool:
        return any(s["name"] == name for s in self.active_statuses)

    def remove_status(self, name: str):
        self.repo.remove_status(self.character.user_id, name)
        self.active_statuses = self.repo.load_active_statuses(self.character.user_id)

    def _apply_immediate_effects(self, name: str):
        if name == "Надорванная воля":
            self.character.stats["STR"] -= 2
        elif name == "Хрупкость плоти":
            self.character.stats["CON"] -= 2
        elif name == "Истощение":
            self.character.max_hp = int(self.character.max_hp * 0.75)
            self.character.hp = min(self.character.hp, self.character.max_hp)