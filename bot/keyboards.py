from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot.texts import Texts

class Keyboards:
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=Texts.BTN_PROFILE), KeyboardButton(text=Texts.BTN_CONTRACTS)],
                [KeyboardButton(text=Texts.BTN_QUEST)],
                [KeyboardButton(text=Texts.BTN_INVENTORY),KeyboardButton(text=Texts.BTN_SHOP)]
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
            # Используем callback_data вида 'complete_<id>'
            buttons.append([InlineKeyboardButton(text=f"✅ {c['name']}", callback_data=f"complete_{c['id']}")])

        buttons.append([InlineKeyboardButton(text="➕ Добавить контракт", callback_data="start_contract")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)