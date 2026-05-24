import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot import handlers_schedule
from core.schedule_job import schedule_checker
# Импорт баз данных и логики ядра
from db.database import Database
from db.template_repo import TemplateRepo
from core.status_registry import StatusRegistry
from core.character_controller import CharacterController
from bot.handlers_shop import router as shop_router

# Импорт роутеров (хэндлеров бота)
from bot.handlers_start import router as start_router
from bot.handlers_profile import router as profile_router
from bot.handlers_habits import router as habits_router
from bot.handlers_contracts import router as contracts_router
from bot.handlers_quests import router as quest_router
from bot.handlers_inventory import router as inventory_router
from bot.texts import Texts

# ==========================================
# КОНФИГУРАЦИЯ БОТА ы
# ==========================================
BOT_TOKEN = "5470429630:AAHr7SitrPYToupP0ukJjt0ZH0LCnDu5GkI"  # Вставьте сюда токен от BotFather
#BOT_TOKEN = "6451320447:AAEFDSNhzpm3Z9ahajLrzi4JbHBaohFrfRE"  # Вставьте сюда токен от BotFather
ADMIN_ID = 505644694

async def main():
    # 1. Включаем базовое логирование, чтобы видеть ошибки в консоли
    logging.basicConfig(level=logging.INFO)

    # 2. Инициализация Базы Знаний (Шаблоны)
    print("Инициализация Базы Данных и выгрузка лора...")
    db_instance = Database("oskolki.db")
    template_repo = TemplateRepo(db_instance)

    # Вытаскиваем все шаблоны баффов/травм из SQLite и кладем в оперативную память
    all_templates = template_repo.load_all_templates()
    StatusRegistry.load(all_templates)

    # 3. Инициализация Контроллера Героя (Singleton)
    print("Пробуждение героя...")
    hero_controller = CharacterController(user_id=ADMIN_ID, db_path="oskolki.db")

    # 4. Настройка Telegram-бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # ВАЖНО: Прокидываем наш контроллер внутрь диспетчера!
    # Благодаря этому `aiogram` сам передаст контроллер в любую функцию-хэндлер,
    # если мы укажем `hero: CharacterController` в её аргументах.
    dp["hero"] = hero_controller

    # 5. Подключение всех модулей (роутеров)
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(habits_router)
    dp.include_router(contracts_router)
    dp.include_router(shop_router)
    dp.include_router(quest_router)
    dp.include_router(inventory_router)
    dp.include_router(handlers_schedule.router)
    print(Texts.BOT_STARTED)

    # Пропускаем старые сообщения, которые накопились пока бот был выключен
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(schedule_checker(bot, db_instance, hero_controller))
    # Запускаем бесконечный цикл прослушивания сообщений
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nРабота бота завершена вручную.")