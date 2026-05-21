from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.texts import Texts
from bot.keyboards import Keyboards
from core.character_controller import CharacterController

router = Router()


@router.message(F.text == Texts.BTN_INVENTORY)
async def show_inventory(message: Message, hero: CharacterController):
    """Выводит сумки героя с кнопками действий."""
    inv_items = hero.inventory.items if isinstance(hero.inventory.items, dict) else (hero.inventory.get_items() or {})
    active_items = {k: v for k, v in inv_items.items() if v > 0}

    if not active_items:
        await message.answer("🎒 <i>Ваш инвентарь пуст.</i>", parse_mode="HTML")
        return

    shop_items = hero.get_shop_items()
    # ИСПРАВЛЕНО: Индексируем базу с удалением пробелов и приведением к нижнему регистру
    items_db = {
        (i.name_text.strip().lower() if hasattr(i, 'name_text') else i['name_text'].strip().lower()): i
        for i in shop_items
    }

    text = "🎒 <b>ВАШ ИНВЕНТАРЬ</b>\n───────────────────────\n<i>Выберите зелье для применения или хлам для продажи.</i>"
    kb = Keyboards.inventory_kb(active_items, items_db)

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("inv_use:"))
async def handle_inventory_use(callback: CallbackQuery, hero: CharacterController):
    """Обрабатывает выпивание зелья."""
    item_id = callback.data.split(":")[1]
    result = await hero.use_potion(item_id)

    await callback.answer(result["message"], show_alert=True)
    if result["success"]:
        await _update_inventory_view(callback, hero)


@router.callback_query(F.data.startswith("inv_sell:"))
async def handle_inventory_sell(callback: CallbackQuery, hero: CharacterController):
    """Обрабатывает продажу обычного предмета."""
    item_id = callback.data.split(":")[1]
    result = await hero.sell_item(item_id)

    await callback.answer(result["message"], show_alert=True)
    if result["success"]:
        await _update_inventory_view(callback, hero)


@router.callback_query(F.data.startswith("inv_sell_raw:"))
async def handle_inventory_sell_raw(callback: CallbackQuery, hero: CharacterController):
    """Запасной хэндлер для предметов, которые потеряли связь со справочником (фолбэк)."""
    item_name = callback.data.split(":")[1]

    # Удаляем вручную и даем 1 золото утешения
    hero._give_item(item_name, -1)
    hero._add_gold(1)
    await hero.save_all()

    await callback.answer(f"Вы продали странный предмет за 1 🌕.", show_alert=True)
    await _update_inventory_view(callback, hero)


async def _update_inventory_view(callback: CallbackQuery, hero: CharacterController):
    """Вспомогательная функция для обновления кнопок после действия."""
    inv_items = hero.inventory.items if isinstance(hero.inventory.items, dict) else (hero.inventory.get_items() or {})
    active_items = {k: v for k, v in inv_items.items() if v > 0}

    if not active_items:
        await callback.message.edit_text("🎒 <i>Ваш инвентарь пуст.</i>", reply_markup=None, parse_mode="HTML")
        return

    shop_items = hero.get_shop_items()
    # Индексируем так же, как при открытии
    items_db = {
        (i.name_text.strip().lower() if hasattr(i, 'name_text') else i['name_text'].strip().lower()): i
        for i in shop_items
    }

    kb = Keyboards.inventory_kb(active_items, items_db)
    await callback.message.edit_reply_markup(reply_markup=kb)