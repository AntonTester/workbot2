import sqlite3


def run_item_migration():
    # Подключаемся к боевой базе данных
    conn = sqlite3.connect("oskolki.db")
    cursor = conn.cursor()

    # Данные нашего нового Зелья бодрости
    item_payload = (
        "energy_potion",  # unique_name
        "Зелье бодрости",  # name_text
        15,  # price
        "potion",  # type
        "Снимает эффект усталости и возвращает силы.",  # effect_desc
        '{"REMOVE_STATUS": "tired"}',  # effects (JSON-строка)
        '["LOOT"]'  # flags (JSON-строка)
    )

    try:
        print("Запуск миграции: добавление 'Зелья бодрости' в лавку...")

        # Выполняем безопасную вставку с обновлением по ключу unique_name
        cursor.execute("""
            INSERT INTO items (unique_name, name_text, price, type, effect_desc, effects, flags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(unique_name) DO UPDATE SET
                name_text = excluded.name_text,
                price = excluded.price,
                type = excluded.type,
                effect_desc = excluded.effect_desc,
                effects = excluded.effects,
                flags = excluded.flags
        """, item_payload)

        conn.commit()
        print("✅ Миграция успешно завершена! Предмет 'energy_potion' добавлен в таблицу items и готов к покупке.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка во время выполнения миграции: {e}")
        print("Изменения были автоматически откачены, база данных не пострадала.")

    finally:
        conn.close()


if __name__ == "__main__":
    run_item_migration()