import json
from dacite import from_dict
from core.models.quest_models import Quest


class QuestRepo:
    def __init__(self, db):
        self.db = db

    def get_active_quest(self, user_id: int) -> Quest | None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quest_data FROM active_quests WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if row and row[0]:
                data = json.loads(row[0])
                return from_dict(data_class=Quest, data=data)
        return None

    def save_quest(self, user_id: int, quest: Quest):
        """Сохраняет прогресс квеста во все колонки таблицы."""
        import dataclasses
        data_json = json.dumps(dataclasses.asdict(quest), ensure_ascii=False)
        flags_json = json.dumps(quest.flags, ensure_ascii=False)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO active_quests (user_id, quest_data, day, flags)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                    quest_data = excluded.quest_data,
                    day = excluded.day,
                    flags = excluded.flags
            """, (user_id, data_json, quest.current_day, flags_json))
            conn.commit()

    def clear_quest(self, user_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_quests WHERE user_id = ?", (user_id,))
            conn.commit()