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

    def add_status(self, user_id: int, name: str, status_type: str, duration_hours: int = None):
        expires_at = None
        if duration_hours:
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=duration_hours)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO statuses (user_id, name, type, expires_at) VALUES (?, ?, ?, ?)",
                           (user_id, name, status_type, expires_at))
            conn.commit()

    def remove_status(self, user_id: int, name: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM statuses WHERE user_id = ? AND name = ?", (user_id, name))
            conn.commit()