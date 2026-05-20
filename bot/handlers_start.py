from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.texts import Texts
from bot.keyboards import Keyboards
from db.database import Database
from db.character_repo import CharacterRepo

router = Router()
db_instance = Database("oskolki.db")


@router.message(CommandStart())
async def cmd_start(message: Message):
    char_repo = CharacterRepo(db_instance)

    # Инициализация профиля в базе, если его еще нет
    _ = char_repo.get_or_create(message.from_user.id)

    # Отправка приветствия и генерация клавиатуры
    await message.answer(
        text=Texts.WELCOME_TEXT,
        reply_markup=Keyboards.main_menu()
    )