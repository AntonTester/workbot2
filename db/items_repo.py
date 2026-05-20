import json


class ItemsRepo:
    """Репозиторий для работы со справочником предметов (магазин и лут)."""

    def __init__(self, db):
        self.db = db

    def get_loot_pool_by_tier(self, tier: str) -> list[str]:
        """Достает из БД предметы нужного тира, парсит JSON-флаги и фильтрует по 'LOOT'."""
        with self.db.get_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            cursor.execute("SELECT name_text, flags FROM items WHERE type = ?", (tier,))
            rows = cursor.fetchall()

        pool = []
        for r in rows:
            # Изолированная грязная работа с JSON
            raw_flags = r.get("flags")
            flags = json.loads(raw_flags) if raw_flags else []

            if "LOOT" in flags:
                pool.append(r["name_text"])

        return pool

    def get_all_shop_items(self) -> list[dict]:
        """Достает все предметы для витрины магазина."""
        with self.db.get_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items")
            return cursor.fetchall()

    def get_item_by_id(self, unique_name: str) -> dict | None:
        """Ищет конкретный предмет по ID (для покупки)."""
        with self.db.get_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items WHERE unique_name = ?", (unique_name,))
            return cursor.fetchone()