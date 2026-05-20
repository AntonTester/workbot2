class ContractRepo:
    def __init__(self, db):
        self.db = db

    def get_active_contracts(self, user_id: int) -> list:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, difficulty, duration, deadline FROM contracts WHERE user_id = ? AND status = 'active'", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_contract(self, contract_id: int) -> dict:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def close_contract(self, contract_id: int, new_status: str = 'completed'):
        """Меняет статус контракта на completed (выполнен) или failed (провален)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE contracts SET status = ? WHERE id = ?", (new_status, contract_id))
            conn.commit()

    def add_contract(self, user_id: int, name: str, difficulty: str, duration: str, deadline: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO contracts (user_id, name, difficulty, duration, deadline) VALUES (?, ?, ?, ?, ?)",
                           (user_id, name, difficulty, duration, deadline))
            conn.commit()