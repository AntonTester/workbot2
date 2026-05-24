import datetime


class ScheduleRepo:
    def __init__(self, db):
        self.db = db

    def save_schedule(self, user_id: int, schedule_data: list):
        """Сохраняет расписание, предварительно удалив старое."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedules WHERE user_id = ?", (user_id,))
            for item in schedule_data:
                cursor.execute("""
                    INSERT INTO schedules (user_id, day_idx, time_str, task_text)
                    VALUES (?, ?, ?, ?)
                """, (user_id, item['day_idx'], item['time_str'], item['task_text']))
            conn.commit()

    def get_user_schedule(self, user_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, day_idx, time_str, task_text FROM schedules WHERE user_id = ? ORDER BY day_idx, time_str",
                (user_id,))
            return [{"id": r['id'], "day_idx": r['day_idx'], "time_str": r['time_str'], "task_text": r['task_text']} for
                    r in cursor.fetchall()]

    def get_next_task(self, user_id: int):
        """Возвращает ближайшую задачу на сегодня."""
        now = datetime.datetime.now()
        day_idx = now.weekday()
        current_time = now.strftime("%H:%M")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, time_str, task_text FROM schedules 
                WHERE user_id = ? AND day_idx = ? AND time_str >= ?
                ORDER BY time_str ASC LIMIT 1
            """, (user_id, day_idx, current_time))
            row = cursor.fetchone()
            return {"id": row['id'], "time_str": row['time_str'], "task_text": row['task_text']} if row else None

    def mark_task_done(self, log_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE schedule_logs SET status = 'done' WHERE id = ?", (log_id,))
            conn.commit()