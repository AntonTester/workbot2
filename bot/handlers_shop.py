from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.texts import Texts
from core.character_controller import CharacterController

router = Router()


@router.message(F.text == Texts.BTN_SHOP)
async def handle_shop(message: Message, hero: CharacterController):
    """Выводит витрину магазина."""
    items = hero.get_shop_items()
    text = Texts.shop_sheet(items, hero.model.gold)

    # Создаем inline-кнопки для покупки
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(
            text=f"Купить {item['name_text']} ({item['price']}💰)",
            callback_data=f"buy_{item['unique_name']}"
        )
    builder.adjust(1)  # Кнопки одна под другой

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("buy_"))
async def handle_buy_callback(callback: CallbackQuery, hero: CharacterController):
    """Обрабатывает нажатие кнопки 'Купить'."""
    item_id = callback.data.split("_")[1]

    # Вызываем метод покупки в контроллере
    result = await hero.buy_item(item_id)

    if result["success"]:
        await callback.answer(f"Вы купили {result['item_name']}! Списано {result['spent']} 💰", show_alert=True)
        # Обновляем витрину, чтобы обновился баланс золота
        items = hero.get_shop_items()
        new_text = Texts.shop_sheet(items, hero.model.gold)
        await callback.message.edit_text(new_text, reply_markup=callback.message.reply_markup, parse_mode="HTML")
    else:
        # Если не хватило золота — показываем ошибку в уведомлении
        await callback.answer(result["error"], show_alert=True)