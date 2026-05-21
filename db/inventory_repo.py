from core.inventory import Inventory

class InventoryRepo:
    def __init__(self, db):
        self.db = db

    def get_inventory(self, character) -> Inventory:
        inv = Inventory(character)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_name, quantity FROM inventory WHERE user_id = ?", (character.user_id,))
            for row in cursor.fetchall():
                inv.items[row['item_name']] = row['quantity']
        return inv

    def save(self, inventory: Inventory):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Собираем ключи для удаления из словаря после итерации
            items_to_remove = []

            for item_name, qty in inventory.items.items():
                if qty <= 0:
                    # Если предметов не осталось — удаляем запись из БД
                    cursor.execute("""
                        DELETE FROM inventory 
                        WHERE user_id = ? AND item_name = ?
                    """, (inventory.character.user_id, item_name))
                    items_to_remove.append(item_name)
                else:
                    # Используем UPSERT (Обновить, если существует, иначе вставить)
                    cursor.execute("""
                        INSERT INTO inventory (user_id, item_name, quantity) 
                        VALUES (?, ?, ?) 
                        ON CONFLICT(user_id, item_name) DO UPDATE SET quantity=excluded.quantity
                    """, (inventory.character.user_id, item_name, qty))

            # Очищаем инвентарь в оперативной памяти от нулей
            for item in items_to_remove:
                del inventory.items[item]

            conn.commit()