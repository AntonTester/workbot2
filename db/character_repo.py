from core.character import Character


class CharacterRepo:
    def __init__(self, db):
        self.db = db

    def get_or_create(self, user_id: int) -> Character:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                cursor.execute("INSERT INTO characters (user_id) VALUES (?)", (user_id,))
                conn.commit()
                return Character(user_id)

            char = Character(user_id, name=row['name'])
            char.hp, char.max_hp, char.xp, char.level, char.gold = row['hp'], row['max_hp'], row['xp'], row['level'], \
            row['gold']
            char.stats = {
                "STR": row['stat_str'], "DEX": row['stat_dex'], "CON": row['stat_con'],
                "INT": row['stat_int'], "WIS": row['stat_wis'], "CHA": row['stat_cha']
            }
            return char

    def save(self, char: Character):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE characters SET 
                    name = ?, hp = ?, max_hp = ?, xp = ?, level = ?, gold = ?,
                    stat_str = ?, stat_dex = ?, stat_con = ?,
                    stat_int = ?, stat_wis = ?, stat_cha = ?
                WHERE user_id = ?
            """, (
                char.name, char.hp, char.max_hp, char.xp, char.level, char.gold,
                char.stats["STR"], char.stats["DEX"], char.stats["CON"],
                char.stats["INT"], char.stats["WIS"], char.stats["CHA"], char.user_id
            ))
            conn.commit()