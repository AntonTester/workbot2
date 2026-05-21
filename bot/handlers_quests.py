from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.texts import Texts
from bot.keyboards import Keyboards  # <--- Импортируем нашу фабрику клавиатур
from core.quest_controller import QuestController
from db.quest_repo import QuestRepo

router = Router()


def get_quest_ctrl(hero_controller) -> QuestController:
    """Вспомогательная функция для инициализации контроллера квестов."""
    return QuestController(hero_controller, QuestRepo(hero_controller.db))


@router.message(F.text == Texts.BTN_QUEST)
async def show_quest_menu(message: Message, hero):
    """Открывает главное меню квеста при нажатии на кнопку в меню."""
    q_ctrl = get_quest_ctrl(hero)

    if not q_ctrl.quest or q_ctrl.quest.status != "active":
        await message.answer(Texts.quest_menu(None), parse_mode="HTML")
        return

    text = Texts.quest_menu(q_ctrl.quest)
    # Используем фабрику клавиатур
    has_actions = bool(q_ctrl.quest.actions)
    kb = Keyboards.quest_main_kb(has_actions)

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "quest_main")
async def back_to_quest_main(callback: CallbackQuery, hero):
    """Возврат в главное меню квеста через inline-кнопку."""
    q_ctrl = get_quest_ctrl(hero)
    text = Texts.quest_menu(q_ctrl.quest)

    has_actions = bool(q_ctrl.quest.actions)
    kb = Keyboards.quest_main_kb(has_actions)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "quest_tasks")
async def show_quest_tasks(callback: CallbackQuery, hero):
    """Выводит список задач, доступных на основе флагов."""
    q_ctrl = get_quest_ctrl(hero)
    tasks = q_ctrl.get_available_tasks()

    if not tasks:
        await callback.answer("Нет доступных задач. Возможно, стоит подождать следующего дня или избавиться от усталости.", show_alert=True)
        return

    # Передаем список задач в фабрику для динамической генерации кнопок
    kb = Keyboards.quest_tasks_kb(tasks)

    await callback.message.edit_text("<b>Доступные задачи:</b>", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("task_info_"))
async def show_task_info(callback: CallbackQuery, hero):
    """Показывает детали задачи и кнопки с возможными проверками навыков."""
    task_name = callback.data.replace("task_info_", "")
    q_ctrl = get_quest_ctrl(hero)

    task = next((t for t in q_ctrl.quest.task_steps if t.name == task_name), None)
    if not task:
        await callback.answer("Задача не найдена.", show_alert=True)
        return

    text = Texts.task_menu(task)

    # Генерация кнопок проверок через фабрику
    kb = Keyboards.quest_task_info_kb(task.name, task.checks)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("check:"))
async def perform_task_check(callback: CallbackQuery, hero):
    """Бросает кубик, начисляет эффекты и выводит D&D результат."""
    # Разбиваем безопасно через двоеточие
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Ошибка чтения данных кнопки.", show_alert=True)
        return

    _, task_name, idx_str = parts
    check_index = int(idx_str)

    q_ctrl = get_quest_ctrl(hero)

    # Делаем бросок через контроллер
    result = await q_ctrl.perform_task_check(task_name, check_index)

    if not result.roll_data:  # Проверка на ошибки (например, квест завершен)
        await callback.answer(result.message, show_alert=True)
        return

    text = Texts.quest_check_result(result)

    # Одиночная кнопка "Назад"
    kb = Keyboards.quest_back_main_kb()

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "quest_next_day")
async def advance_quest_day(callback: CallbackQuery, hero):
    """Срабатывает при нажатии на кнопку Следующий день."""
    q_ctrl = get_quest_ctrl(hero)
    result = q_ctrl.process_daily_event()

    # Если квеста нет
    if not result.success:
        await callback.answer(result.message, show_alert=True)
        return

    # Если наступил лимит дней и квест провален
    if result.is_failed:
        text = f"🌑 <b>Время вышло!</b>\nКвест «{q_ctrl.quest.quest_name}» провален."
        await callback.message.edit_text(text, reply_markup=Keyboards.quest_back_main_kb(), parse_mode="HTML")
        return

    # Выводим текстовый эвент
    text = Texts.daily_event_message(result.day, result.step_title, result.step_desc)
    await callback.message.edit_text(text, reply_markup=Keyboards.quest_event_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "quest_actions")
async def show_quest_actions(callback: CallbackQuery, hero):
    """Открывает магазин квестовых усилителей."""
    q_ctrl = get_quest_ctrl(hero)

    if not q_ctrl.quest or q_ctrl.quest.status != "active":
        await callback.answer("Нет активного квеста.", show_alert=True)
        return

    actions = q_ctrl.quest.actions
    if not actions:
        await callback.answer("Для этого квеста нет доступных усилений.", show_alert=True)
        return

    text = "🛒 <b>ПОДГОТОВКА К ЗАДАЧАМ</b>\n───────────────────────\n<i>Здесь вы можете приобрести инструменты, которые дадут бонус к броскам.</i>"
    kb = Keyboards.quest_actions_kb(actions)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("quest_buy:"))
async def buy_quest_action(callback: CallbackQuery, hero):
    """Покупка усилителя."""
    action_name = callback.data.split(":")[1]
    q_ctrl = get_quest_ctrl(hero)

    result = await q_ctrl.buy_action(action_name)

    if result.success:
        await callback.answer(result.message, show_alert=True)
        # Перекидываем обратно в меню квеста, чтобы отобразился купленный бонус
        await back_to_quest_main(callback, hero)
    else:
        # Не хватило золота
        await callback.answer(result.message, show_alert=True)