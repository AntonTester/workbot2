import random
from core.status_registry import StatusRegistry


class RewardManager:
    """
    Менеджер динамической выдачи лута и применения предметов.
    Не содержит жестко закодированных списков предметов — всё берется из БД.
    """

    @staticmethod
    def grant_tiered_loot(hero_controller, tier: str, count: int = 1) -> list[str]:
        """
        Динамически выдает предметы указанного тира (precious, component, potion, junk).
        Обращается к ItemsRepo, который достает предметы из БД и проверяет флаг 'LOOT'.
        """
        if count <= 0:
            return []

        # Запрашиваем готовый и отфильтрованный пул у репозитория
        pool = hero_controller.items_repo.get_loot_pool_by_tier(tier)

        if not pool:
            return []

        found_items = []
        for _ in range(count):
            item = random.choice(pool)
            hero_controller._give_item(item, 1)
            found_items.append(item)

        return found_items

    @staticmethod
    def use_healing_potion(hero_controller) -> tuple[int, int]:
        """
        Применяет Зелье лечения.
        Логика D&D: Восстанавливает 1d6 + модификатор Телосложения (CON).
        """
        from core.game_calculator import GameCalculator

        roll_val = random.randint(1, 6)
        base_con = hero_controller.model.stats.get("CON", 10)
        # Получаем чистый модификатор (эффекты отключены, передаем 0)
        _, con_mod = GameCalculator.calculate_stat_modifier(base_con, 0)

        total_heal = max(1, roll_val + con_mod)
        hero_controller._modify_hp(total_heal)

        return total_heal, con_mod

    @staticmethod
    def use_cure_disease_potion(hero_controller) -> str | None:
        """Находит все активные болезни на персонаже и снимает одну случайную."""
        # Поддержка как словарей, так и объектов в active_statuses
        diseases = [s for s in hero_controller.active_statuses if
                    (s.type if hasattr(s, 'type') else s["type"]) == "disease"]

        if not diseases:
            return None

        target_disease = random.choice(diseases)
        name_key = target_disease.name if hasattr(target_disease, 'name') else target_disease["name"]

        hero_controller._remove_status(name_key)

        template = StatusRegistry.get(name_key)
        return template.name_text if template else name_key

    @staticmethod
    def grant_random_status(hero_controller, status_type: str, count: int = 1, duration: int = None) -> list[str]:
        """
        Случайным образом выбирает и накладывает статусы из глобального реестра.
        """
        if count <= 0:
            return []

        pool = []
        if status_type == "buff":
            pool = StatusRegistry.get_all_buffs()
        elif status_type == "disease":
            pool = StatusRegistry.get_all_diseases()
        elif status_type == "injury":
            pool = StatusRegistry.get_all_injuries()

        if not pool:
            return []

        applied_names = []
        for _ in range(count):
            status_id = random.choice(pool)
            # Контроллер сам обратится к StatusRepo для стакания/добавления статуса
            if hero_controller._apply_status(status_id, duration):
                applied_names.append(StatusRegistry.get(status_id).name_text)

        return applied_names