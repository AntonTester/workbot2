import datetime


class StatusRepo:
    def __init__(self, db):
        self.db = db

    def load_active_statuses(self, user_id: int) -> list:
        now = datetime.datetime.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM statuses WHERE user_id = ? AND expires_at < ?", (user_id, now))
            conn.commit()

            cursor.execute("SELECT name, type, expires_at FROM statuses WHERE user_id = ?", (user_id,))
            return [{"name": row["name"], "type": row["type"], "expires_at": row["expires_at"]} for row in
                    cursor.fetchall()]

    def add_status(self, user_id: int, name: str, type_str: str, duration_hours=None):
        """Добавляет бессрочный статус персонажу. Игнорирует дубликаты."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Если такой статус уже есть (срабатывает UNIQUE), команда DO NOTHING
            # просто отменит добавление без вызова ошибки базы данных.
            cursor.execute("""
                INSERT INTO statuses (user_id, name, type)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, name) DO NOTHING
            """, (user_id, name, type_str))

            conn.commit()

    def remove_status(self, user_id: int, name: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM statuses WHERE user_id = ? AND name = ?", (user_id, name))
            conn.commit()