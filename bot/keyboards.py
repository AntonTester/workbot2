from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot.texts import Texts
from core.game_calculator import GameCalculator


class Keyboards:
    """Фабрика для создания всех клавиатур бота."""

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=Texts.BTN_PROFILE), KeyboardButton(text=Texts.BTN_CONTRACTS)],
                [KeyboardButton(text=Texts.BTN_QUEST)],
                [KeyboardButton(text=Texts.BTN_INVENTORY), KeyboardButton(text=Texts.BTN_SHOP)]
            ],
            resize_keyboard=True,
            is_persistent=True
        )

    @staticmethod
    def contract_draft_kb(diff_idx: int, dur_idx: int, day_idx: int) -> InlineKeyboardMarkup:
        """Клавиатура-переключатель для настроек контракта."""
        diff_text = Texts.DIFFICULTIES[diff_idx]
        dur_text = Texts.DURATIONS[dur_idx]
        day_text = Texts.get_deadline_options()[day_idx]

        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🩸 Сложность: {diff_text}", callback_data="toggle_diff")],
            [InlineKeyboardButton(text=f"⏳ Время: {dur_text}", callback_data="toggle_dur")],
            [InlineKeyboardButton(text=f"📅 Дедлайн: {day_text}", callback_data="toggle_day")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_contract")]
        ])

    @staticmethod
    def board_menu(contracts: list) -> InlineKeyboardMarkup:
        """Динамически создает кнопки выполнения для каждого контракта."""
        buttons = []
        for c in contracts:
            buttons.append([InlineKeyboardButton(text=f"✅ {c['name']}", callback_data=f"complete_{c['id']}")])

        buttons.append([InlineKeyboardButton(text="➕ Добавить контракт", callback_data="start_contract")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    # ==========================================
    # КЛАВИАТУРЫ КВЕСТОВ
    # ==========================================

    @staticmethod
    def shop_kb(items: list) -> InlineKeyboardMarkup:
        """Клавиатура для покупки предметов в лавке."""
        buttons = []
        for item in items:
            # Поддерживаем как словари из БД, так и возможные объекты
            name = item['name_text'] if isinstance(item, dict) else item.name_text
            price = item['price'] if isinstance(item, dict) else item.price
            unique_name = item['unique_name'] if isinstance(item, dict) else item.unique_name

            buttons.append([InlineKeyboardButton(text=f"Купить {name} ({price}🌕)", callback_data=f"buy_{unique_name}")])

        return InlineKeyboardMarkup(inline_keyboard=buttons)
    @staticmethod
    def quest_tasks_kb(tasks: list) -> InlineKeyboardMarkup:
        """Список доступных задач в рамках квеста."""
        buttons = []
        for task in tasks:
            buttons.append(
                [InlineKeyboardButton(text=f"▶️ {task.display_name}", callback_data=f"task_info_{task.name}")])

        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="quest_main")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def quest_task_info_kb(task_name: str, checks: list) -> InlineKeyboardMarkup:
        """Кнопки с проверками навыков для конкретной задачи."""
        # Словарь склонений для красивого вывода кнопок (Винительный падеж)
        ACCUSATIVE_SKILLS = {
            "Атлетика": "атлетику", "Акробатика": "акробатику", "Магия": "магию",
            "История": "историю", "Природа": "природу", "Религия": "религию",
            "Медицина": "медицину"
        }

        buttons = []
        for idx, check in enumerate(checks):
            skill_lower = check.skill.lower().strip()
            skill_ru = GameCalculator.SKILL_MAP.get(skill_lower, (check.skill, ""))[0]

            # Склоняем навык, а если его нет в словаре (например, "Обман") — просто пишем с маленькой буквы
            skill_acc = ACCUSATIVE_SKILLS.get(skill_ru, skill_ru.lower())

            btn_text = f"Применить {skill_acc}"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"check:{task_name}:{idx}")])

        buttons.append([InlineKeyboardButton(text="🔙 К задачам", callback_data="quest_tasks")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def inventory_kb(inv_items: dict, items_db: dict) -> InlineKeyboardMarkup:
        """Клавиатура инвентаря: зелья можно выпить, остальное - продать."""
        buttons = []
        for item_name, quantity in inv_items.items():
            if quantity <= 0: continue

            # Защита от пробелов и регистра при поиске
            search_key = item_name.strip().lower()
            item_def = items_db.get(search_key)

            # Если предмета по какой-то причине нет в справочнике, не скрываем его!
            # Выводим как обычный хлам за 1 золото.
            if not item_def:
                safe_name = item_name[:30]  # Обрезаем на случай лимитов Telegram
                buttons.append([InlineKeyboardButton(text=f"🌕 Продать {item_name} (x{quantity}) за 1 🌕",
                                                     callback_data=f"inv_sell_raw:{safe_name}")])
                continue

            unique_name = item_def.get("unique_name") if isinstance(item_def, dict) else getattr(item_def,
                                                                                                 "unique_name")
            i_type = item_def.get("type") if isinstance(item_def, dict) else getattr(item_def, "type", "junk")
            i_price = item_def.get("price", 0) if isinstance(item_def, dict) else getattr(item_def, "price", 0)

            if i_type == "potion":
                buttons.append([InlineKeyboardButton(text=f"🧪 Выпить {item_name} (x{quantity})",
                                                     callback_data=f"inv_use:{unique_name}")])
            else:
                sell_price = max(1, i_price // 2)
                buttons.append([InlineKeyboardButton(text=f"🌕 Продать {item_name} (x{quantity}) за {sell_price} з.",
                                                     callback_data=f"inv_sell:{unique_name}")])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def quest_back_main_kb() -> InlineKeyboardMarkup:
        """Одиночная кнопка возврата после броска кубиков."""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться к квесту", callback_data="quest_main")]
        ])

    @staticmethod
    def quest_main_kb(has_actions: bool) -> InlineKeyboardMarkup:
        """Главное меню активного квеста."""
        buttons = [
            [InlineKeyboardButton(text="📜 Доступные задачи", callback_data="quest_tasks")],
            [InlineKeyboardButton(text="🌅 Следующий день", callback_data="quest_next_day")]
        ]
        if has_actions:
            buttons.append([InlineKeyboardButton(text="🛒 Подготовка (Усилители)", callback_data="quest_actions")])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def quest_event_kb() -> InlineKeyboardMarkup:
        """Одиночная кнопка после прочтения эвента нового дня."""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Понятно", callback_data="quest_main")]
        ])


    @staticmethod
    def quest_actions_kb(actions: list) -> InlineKeyboardMarkup:
        """Клавиатура покупки усилителей в квесте."""
        buttons = []
        for action in actions:
            buttons.append([InlineKeyboardButton(text=f"Купить {action.display_name} ({action.price}🌕)",
                                                 callback_data=f"quest_buy:{action.name}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад к квесту", callback_data="quest_main")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)