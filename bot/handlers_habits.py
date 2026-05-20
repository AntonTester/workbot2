from aiogram import Router, F
from aiogram.types import Message
from bot.texts import Texts
from core.character_controller import CharacterController

router = Router()


@router.message(F.text == Texts.BTN_RITUAL)
async def handle_ritual(message: Message, hero: CharacterController):
    # Теперь контроллер возвращает словарь с деталями ритуала
    result = await hero.perform_ritual()

    # Передаем объект RollData в форматер броска
    roll_text = Texts.format_roll(result["roll"])

    # Передаем весь словарь в форматер текста
    result_text = Texts.ritual_result(result)

    await message.answer(f"{result_text}\n\n{roll_text}", parse_mode="HTML")

@router.message(F.text == Texts.BTN_CORRUPTION)
async def handle_corruption(message: Message, hero: CharacterController):
    # Контроллер возвращает словарь с деталями
    result = await hero.succumb_to_corruption()

    # Передаем только объект RollData (result["roll"]) в форматер броска
    roll_text = Texts.format_roll(result["roll"])

    # Передаем весь словарь (result) в форматер текста
    result_text = Texts.corruption_result(hero.model.hp, hero.model.max_hp, result)

    await message.answer(f"{result_text}\n\n{roll_text}", parse_mode="HTML")