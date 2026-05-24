import sqlite3


def run_schedule_migration():
    conn = sqlite3.connect("oskolki.db")
    cursor = conn.cursor()

    try:
        print("Начинаем миграцию расписания...")

        # Таблица самого расписания
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_idx INTEGER, -- 0=ПН, 6=ВС
                time_str TEXT,   -- 'HH:MM'
                task_text TEXT
            )
        """)

        # Таблица логов на сегодня (чтобы отслеживать, уведомили или оштрафовали)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                schedule_id INTEGER,
                log_date DATE,
                status TEXT -- 'notified', 'damaged', 'done'
            )
        """)

        # Добавляем валюту "Звездочки", если ее нет (перехватываем ошибку, если уже есть)
        try:
            cursor.execute("ALTER TABLE characters ADD COLUMN stars INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует

        conn.commit()
        print("✅ Миграция расписания успешно завершена!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_schedule_migration()