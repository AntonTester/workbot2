import json
from dacite import from_dict
from core.models.quest_models import Quest


class QuestRepo:
    """
    Репозиторий для работы с активными квестами пользователя.
    Использует JSON-сериализацию для хранения сложной вложенной структуры квеста (DataClasses).
    """

    def __init__(self, db):
        self.db = db

    def get_active_quest(self, user_id: int) -> Quest | None:
        """Извлекает квест из БД и собирает его обратно в строго типизированный объект Quest."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quest_data FROM active_quests WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if row and row[0]:
                data = json.loads(row[0])
                # dacite.from_dict автоматически собирает все вложенные датаклассы (TaskStep, Check и т.д.)
                return from_dict(data_class=Quest, data=data)

        return None

    def save_quest(self, user_id: int, quest: Quest):
        """Сохраняет прогресс квеста, превращая объект в JSON-строку."""
        import dataclasses

        # Преобразуем датакласс со всеми вложенностями в словарь, а затем в JSON
        data_json = json.dumps(dataclasses.asdict(quest), ensure_ascii=False)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO active_quests (user_id, quest_data)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET quest_data = excluded.quest_data
            """, (user_id, data_json))
            conn.commit()

    def clear_quest(self, user_id: int):
        """Удаляет квест после его полного завершения или провала."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_quests WHERE user_id = ?", (user_id,))
            conn.commit()