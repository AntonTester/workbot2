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
            # Используем UPSERT (Обновить, если существует, иначе вставить)
            for item_name, qty in inventory.items.items():
                cursor.execute("""
                    INSERT INTO inventory (user_id, item_name, quantity) 
                    VALUES (?, ?, ?) 
                    ON CONFLICT(user_id, item_name) DO UPDATE SET quantity=excluded.quantity
                """, (inventory.character.user_id, item_name, qty))
            conn.commit()