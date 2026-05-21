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
        buttons = []
        for idx, check in enumerate(checks):
            # Подтягиваем русское название навыка из калькулятора
            skill_lower = check.skill.lower().strip()
            skill_ru = GameCalculator.SKILL_MAP.get(skill_lower, (check.skill, ""))[0]

            # Формируем кнопку. Используем двоеточие в callback_data
            btn_text = f"[{skill_ru}] {check.display_name} (Сл: {check.difficulty})"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"check:{task_name}:{idx}")])

        buttons.append([InlineKeyboardButton(text="🔙 К задачам", callback_data="quest_tasks")])
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