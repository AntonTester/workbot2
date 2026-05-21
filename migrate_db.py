import sqlite3


def run_migration():
    # Подключаемся к нашей боевой базе
    conn = sqlite3.connect("oskolki.db")
    cursor = conn.cursor()

    try:
        print("Начинаем миграцию...")

        # 1. Сначала удаляем существующие дубли статусов у игроков
        # (оставляем только запись с максимальным id, то есть самую свежую)
        cursor.execute("""
            DELETE FROM statuses
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM statuses
                GROUP BY user_id, name
            )
        """)
        print("Дубликаты успешно вычищены.")

        # 2. Создаем новую временную таблицу с правильным UNIQUE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statuses_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                type TEXT,
                expires_at TIMESTAMP,
                UNIQUE(user_id, name)
            )
        """)

        # 3. Переливаем очищенные данные из старой таблицы в новую
        cursor.execute("INSERT INTO statuses_new SELECT * FROM statuses")

        # 4. Удаляем старую таблицу и переименовываем новую на её место
        cursor.execute("DROP TABLE statuses")
        cursor.execute("ALTER TABLE statuses_new RENAME TO statuses")

        conn.commit()
        print("✅ Миграция успешно завершена! Таблица statuses обновлена.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка миграции: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()