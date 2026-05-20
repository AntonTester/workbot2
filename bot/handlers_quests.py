from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.texts import Texts
from core.quest_controller import QuestController
from db.quest_repo import QuestRepo

router = Router()


# Вспомогательная функция для сборки контроллера (зависит от твоей точки входа)
def get_quest_ctrl(hero_controller) -> QuestController:
    return QuestController(hero_controller, QuestRepo(hero_controller.db))


@router.message(F.text == Texts.BTN_QUEST)
async def show_quest_menu(message: Message, hero):
    """Открывает главное меню квеста."""
    q_ctrl = get_quest_ctrl(hero)

    if not q_ctrl.quest or q_ctrl.quest.status != "active":
        await message.answer(Texts.quest_menu(None, hero.model.energy, hero.model.max_energy), parse_mode="HTML")
        return

    text = Texts.quest_menu(q_ctrl.quest, hero.model.energy, hero.model.max_energy)

    # Кнопки для Доступных задач и Магазина квеста
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Доступные задачи", callback_data="quest_tasks")
    if q_ctrl.quest.actions:
        builder.button(text="🛒 Подготовка (Усилители)", callback_data="quest_actions")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "quest_tasks")
async def show_quest_tasks(callback: CallbackQuery, hero):
    """Выводит список задач, доступных на основе флагов."""
    q_ctrl = get_quest_ctrl(hero)
    tasks = q_ctrl.get_available_tasks()

    if not tasks:
        await callback.answer("Нет доступных задач. Возможно, стоит подождать следующего дня.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(text=f"▶️ {task.display_name}", callback_data=f"task_info_{task.name}")

    builder.button(text="🔙 Назад", callback_data="quest_main")
    builder.adjust(1)

    await callback.message.edit_text("<b>Доступные задачи:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("task_info_"))
async def show_task_info(callback: CallbackQuery, hero):
    """Показывает детали задачи и кнопки с проверками навыков."""
    task_name = callback.data.replace("task_info_", "")
    q_ctrl = get_quest_ctrl(hero)

    task = next((t for t in q_ctrl.quest.task_steps if t.name == task_name), None)
    if not task:
        await callback.answer("Задача не найдена.", show_alert=True)
        return

    text = Texts.task_menu(task)

    builder = InlineKeyboardBuilder()
    for idx, check in enumerate(task.checks):
        # Кнопка формата: [Убеждение] Договориться со стражей (Сложность: 15) | ⚡ 5
        btn_text = f"[{check.skill}] {check.display_name} (Сл: {check.difficulty}) | ⚡ {check.energy}"
        builder.button(text=btn_text, callback_data=f"check_{task.name}_{idx}")

    builder.button(text="🔙 К задачам", callback_data="quest_tasks")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("check_"))
async def perform_task_check(callback: CallbackQuery, hero):
    """Бросает кубик, тратит энергию и выводит D&D результат."""
    _, task_name, idx_str = callback.data.split("_", 2)
    check_index = int(idx_str)

    q_ctrl = get_quest_ctrl(hero)

    # Делаем бросок через контроллер
    result = await q_ctrl.perform_task_check(task_name, check_index)

    if not result.roll_data:  # Если проверка не прошла по энергии или ошибке
        await callback.answer(result.message, show_alert=True)
        return

    # Формируем красивый D&D лог
    text = Texts.quest_check_result(result)

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Вернуться к квесту", callback_data="quest_main")

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "quest_main")
async def back_to_quest_main(callback: CallbackQuery, hero):
    """Возврат в главное меню квеста."""
    q_ctrl = get_quest_ctrl(hero)
    text = Texts.quest_menu(q_ctrl.quest, hero.model.energy, hero.model.max_energy)

    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Доступные задачи", callback_data="quest_tasks")
    if q_ctrl.quest.actions:
        builder.button(text="🛒 Подготовка (Усилители)", callback_data="quest_actions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")