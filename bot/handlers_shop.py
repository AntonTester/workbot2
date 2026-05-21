from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.texts import Texts
from core.character_controller import CharacterController

router = Router()

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.texts import Texts
from bot.keyboards import Keyboards
from core.character_controller import CharacterController

router = Router()


@router.message(F.text == Texts.BTN_SHOP)
async def handle_shop(message: Message, hero: CharacterController):
    """Выводит витрину магазина."""
    items = hero.get_shop_items()
    text = Texts.shop_sheet(items, hero.model.gold)

    # Используем фабрику клавиатур вместо ручной сборки
    kb = Keyboards.shop_kb(items)

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("buy_"))
async def handle_buy_callback(callback: CallbackQuery, hero: CharacterController):
    """Обрабатывает нажатие кнопки 'Купить'."""
    # Безопасный сплит на случай, если в уникальном имени есть нижние подчеркивания
    item_id = callback.data.split("_", 1)[1]

    # Вызываем метод покупки в контроллере (возвращает объект PurchaseResult)
    result = await hero.buy_item(item_id)

    # ОБНОВЛЕНО: Обращаемся к полям датакласса через точку
    if result.success:
        await callback.answer(f"Вы купили {result.item_name}! Списано {result.spent} 🌕", show_alert=True)

        # Обновляем витрину, чтобы обновился баланс золота
        items = hero.get_shop_items()
        new_text = Texts.shop_sheet(items, hero.model.gold)
        kb = Keyboards.shop_kb(items)

        await callback.message.edit_text(new_text, reply_markup=kb, parse_mode="HTML")
    else:
        # Если не хватило золота — показываем ошибку в уведомлении
        await callback.answer(result.error, show_alert=True)
