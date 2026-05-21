import json
from core.status_registry import Buff, Injury, Disease, Debuff, StatusFlag  # <--- Добавлен импорт Debuff


class TemplateRepo:
    """Репозиторий для выгрузки справочника состояний из БД."""

    def __init__(self, db):
        self.db = db

    def load_all_templates(self) -> dict:
        """Извлекает все шаблоны из БД и собирает их в словарь."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM status_templates")
            rows = cursor.fetchall()

        templates = {}
        for r in rows:
            # Превращаем JSON-строку флагов обратно в Enum
            raw_flags = json.loads(r['flags']) if r['flags'] else []
            flags = [StatusFlag(f) for f in raw_flags]

            # Читаем новую колонку с эффектами и парсим JSON
            effects = json.loads(r['effects']) if 'effects' in r.keys() and r['effects'] else {}

            # Собираем нужный класс в зависимости от колонки type
            if r['type'] == 'buff':
                templates[r['unique_name']] = Buff(
                    r['unique_name'], r['name_text'], r['description'], r['effect'], flags, effects
                )
            elif r['type'] == 'injury':
                templates[r['unique_name']] = Injury(
                    r['unique_name'], r['name_text'], r['description'], r['effect'], flags, effects
                )
            elif r['type'] == 'disease':
                templates[r['unique_name']] = Disease(
                    r['unique_name'], r['name_text'], r['description'], r['effect'], r['duration_days'], flags, effects
                )
            elif r['type'] == 'debuff':
                # Дебаффы из квестов. У них тоже есть duration_days (длительность), поэтому передаем её
                templates[r['unique_name']] = Debuff(
                    r['unique_name'], r['name_text'], r['description'], r['effect'], r['duration_days'], flags, effects
                )

        return templates