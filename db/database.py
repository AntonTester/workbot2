import sqlite3

class Database:
    def __init__(self, db_path: str = "oskolki.db"):
        self.db_path = db_path
        self._create_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS characters (
                                user_id INTEGER PRIMARY KEY,
                                name TEXT DEFAULT 'Астра Лисмор',
                                hp INTEGER DEFAULT 9,
                                max_hp INTEGER DEFAULT 9,
                                energy INTEGER DEFAULT 5,      -- Текущая энергия
                                max_energy INTEGER DEFAULT 5,  -- Максимум энергии
                                xp INTEGER DEFAULT 0, 
                                level INTEGER DEFAULT 1, 
                                gold INTEGER DEFAULT 0,
                                stat_str INTEGER DEFAULT 8,
                                stat_dex INTEGER DEFAULT 14,
                                stat_con INTEGER DEFAULT 12,
                                stat_int INTEGER DEFAULT 14,
                                stat_wis INTEGER DEFAULT 16,
                                stat_cha INTEGER DEFAULT 12
                            )
                        """)

            # Таблица шаблонов квестов (хранит JSON)
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS quests (
                                quest_id TEXT PRIMARY KEY,
                                data_json TEXT
                            )
                        """)

            # Таблица активного прогресса пользователя
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS active_quests (
                                user_id INTEGER PRIMARY KEY,
                                quest_data TEXT
                            )
                        """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    type TEXT,
                    expires_at TIMESTAMP
                )
            """)
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS inventory (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER,
                                item_name TEXT,
                                quantity INTEGER DEFAULT 1,
                                UNIQUE(user_id, item_name)  -- Вот эта строчка решает проблему!
                            )
                        """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    difficulty TEXT,
                    duration TEXT,
                    deadline TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS status_templates (
                    unique_name TEXT PRIMARY KEY,
                    type TEXT,
                    name_text TEXT,
                    description TEXT,
                    effect TEXT,
                    duration_days INTEGER DEFAULT 0,
                    flags TEXT DEFAULT '[]',
                    effects TEXT DEFAULT '{}'
                )
            """)
            # Таблица предметов теперь включает колонку flags
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    unique_name TEXT PRIMARY KEY,
                    name_text TEXT,
                    price INTEGER,
                    type TEXT,
                    effect_desc TEXT,
                    effects TEXT DEFAULT '{}',
                    flags TEXT DEFAULT '[]'
                )
            """)
            self._seed_templates(conn)
            self._seed_items(conn)

    def _seed_templates(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM status_templates")
        if cursor.fetchone()[0] == 0:
            default_templates = [
                # ✨ БАФФЫ
                ("iron_will", "buff", "Крепкая воля", "Ваш разум непоколебим.", "+2 к проверкам Мудрости", "[]", 0,
                 '{"ROLL_BONUS_WIS": 2}'),
                ("cats_grace", "buff", "Грация кошки", "Ваши движения неуловимы.", "+2 к проверкам Ловкости", "[]", 0,
                 '{"ROLL_BONUS_DEX": 2}'),
                ("lions_endurance", "buff", "Стойкость льва", "Ваша плоть не знает усталости.",
                 "+2 к проверкам Выносливости", "[]", 0, '{"ROLL_BONUS_CON": 2}'),
                ("foxs_cunning", "buff", "Хитрость лисы", "Вы подмечаете мельчайшие детали.",
                 "+2 к проверкам Интеллекта",
                 "[]", 0, '{"ROLL_BONUS_INT": 2}'),
                ("eagles_splendor", "buff", "Великолепие орла", "Ваша аура внушает трепет.", "+2 к проверкам Харизмы",
                 "[]",
                 0, '{"ROLL_BONUS_CHA": 2}'),

                # 🩸 ТРАВМЫ (Лорные)

            ]
            cursor.executemany("""
                INSERT INTO status_templates (unique_name, type, name_text, description, effect, flags, duration_days, effects)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, default_templates)
            conn.commit()

    def _seed_items(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        if cursor.fetchone()[0] == 0:
            default_items = [
                # 🧪 Зелья
                (
                "healing_potion", "Эликсир живой крови", 25, "potion", "Восстанавливает плоть.", '{"HEAL_DICE": "1d6"}',
                '["LOOT"]'),
                ("cure_disease_potion", "Слеза очищения", 50, "potion", "Смывает заразу с души и тела.",
                 '{"CURE_DISEASE": 1}', '["LOOT"]'),

                # 💎 Драгоценности
                ("ruby", "Идеальный рубин", 100, "precious", "Камень, пылающий внутренним огнем.", '{}', '["LOOT"]'),
                ("diamond", "Ограненный алмаз", 150, "precious", "Осколок первозданного света.", '{}', '["LOOT"]'),
                ("sapphire", "Око Бездны", 120, "precious", "Глубокий синий сапфир, в котором тонет взгляд.", '{}',
                 '["LOOT"]'),

                # 🔮 Магические компоненты
                ("focus_shard", "Осколок души", 15, "component", "Пульсирующий магический кристалл.", '{}', '["LOOT"]'),
                ("concentration_core", "Пылающее ядро", 25, "component", "Сгусток чистой энергии.", '{}', '["LOOT"]'),
                ("time_ingot", "Астральное серебро", 35, "component", "Металл, не подвластный старению.", '{}',
                 '["LOOT"]'),
                (
                    "ethereal_dust", "Эфирная пыль", 20, "component", "Светящаяся субстанция из иных миров.", '{}',
                    '["LOOT"]'),

                # 🗑 Хлам
                ("junk_dust", "Прах мертвеца", 1, "junk", "Серый пепел неизвестного происхождения.", '{}', '["LOOT"]'),
                ("junk_quill", "Истлевшее перо", 2, "junk", "Разваливается от одного касания.", '{}', '["LOOT"]'),
                ("junk_gear", "Ржавый гвоздь", 3, "junk", "Ни на что не годен.", '{}', '["LOOT"]'),
                (
                "junk_glass", "Осколок мутного стекла", 1, "junk", "Осторожно, можно порезать руку.", '{}', '["LOOT"]'),
                ("junk_parchment", "Обрывок древнего свитка", 2, "junk", "Руны давно стерлись.", '{}', '["LOOT"]'),
                ("junk_flower", "Мертвый цветок", 1, "junk", "Почерневшие сухие лепестки.", '{}', '["LOOT"]'),
                ("junk_vial", "Треснувший флакон", 3, "junk", "На дне запеклась странная слизь.", '{}', '["LOOT"]'),
                ("junk_knife", "Ржавый кинжал", 4, "junk", "Лезвие давно изъедено коррозией.", '{}', '["LOOT"]'),
                ("junk_sack", "Прогнивший мешочек", 2, "junk", "Ткань разлезается по швам.", '{}', '["LOOT"]'),
                ("junk_bone", "Крысиная кость", 1, "junk", "Обычная старая кость.", '{}', '["LOOT"]')
            ]

            cursor.executemany("""
                INSERT INTO items (unique_name, name_text, price, type, effect_desc, effects, flags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, default_items)
            conn.commit()