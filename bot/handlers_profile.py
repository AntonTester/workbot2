from aiogram import Router, F
from aiogram.types import Message

from bot.texts import Texts
from core.character_controller import CharacterController

router = Router()

@router.message(F.text == Texts.BTN_PROFILE)
async def handle_profile(message: Message, hero: CharacterController):
    # Генерируем D&D лист, используя состояние Героя из памяти
    profile_text = Texts.profile_sheet(hero)

    # Отправляем с включенным HTML парсингом, чтобы работали теги <b> и <i>
    await message.answer(profile_text, parse_mode="HTML")