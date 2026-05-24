import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.texts import Texts
from bot.keyboards import Keyboards
from db.schedule_repo import ScheduleRepo

router = Router()


class ScheduleState(StatesGroup):
    waiting_for_schedule = State()


DAYS_MAP = {"ПН": 0, "ВТ": 1, "СР": 2, "ЧТ": 3, "ПТ": 4, "СБ": 5, "ВС": 6}


@router.message(F.text == "🗓 Расписание")
async def show_schedule_menu(message: Message, hero):
    repo = ScheduleRepo(hero.db)
    sched = repo.get_user_schedule(hero.model.user_id)
    next_task = repo.get_next_task(hero.model.user_id)

    text = Texts.schedule_main(next_task)
    kb = Keyboards.schedule_menu_kb(bool(sched))
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "sched_show")
async def show_full_schedule(callback: CallbackQuery, hero):
    repo = ScheduleRepo(hero.db)
    sched = repo.get_user_schedule(hero.model.user_id)

    text = "📋 <b>ВАШЕ РАСПИСАНИЕ:</b>\n"
    current_day = -1
    days_reverse = {v: k for k, v in DAYS_MAP.items()}

    for s in sched:
        if s['day_idx'] != current_day:
            current_day = s['day_idx']
            text += f"\n<b>{days_reverse[current_day]}</b>\n"
        text += f"  {s['time_str']} - {s['task_text']}\n"

    await callback.message.edit_text(text, parse_mode="HTML")


@router.callback_query(F.data == "sched_new")
async def ask_new_schedule(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте новое расписание в формате:\n\nПН\n9:00 Подъем\n9:30 Завтрак\n...")
    await state.set_state(ScheduleState.waiting_for_schedule)
    await callback.answer()


@router.message(ScheduleState.waiting_for_schedule)
async def parse_schedule(message: Message, state: FSMContext, hero):
    lines = message.text.split('\n')
    parsed_data = []
    current_day = -1

    for line in lines:
        line = line.strip()
        if not line: continue

        upper_line = line.upper()
        if upper_line in DAYS_MAP:
            current_day = DAYS_MAP[upper_line]
            continue

        match = re.match(r"^(\d{1,2}:\d{2})\s+(.+)$", line)
        if match and current_day != -1:
            time_str, task_text = match.groups()
            # Форматируем время к виду 09:00
            time_str = f"{int(time_str.split(':')[0]):02d}:{time_str.split(':')[1]}"
            parsed_data.append({"day_idx": current_day, "time_str": time_str, "task_text": task_text})

    if not parsed_data:
        await message.answer("Не удалось распознать расписание. Проверьте формат.")
        return

    repo = ScheduleRepo(hero.db)
    repo.save_schedule(hero.model.user_id, parsed_data)
    await state.clear()
    await message.answer("✅ Расписание успешно сохранено!")


@router.callback_query(F.data.startswith("sched_done:"))
async def mark_task_done(callback: CallbackQuery, hero):
    log_id = int(callback.data.split(":")[1])
    repo = ScheduleRepo(hero.db)

    # Отмечаем в БД
    repo.mark_task_done(log_id)

    # Выдаем награду (требуется добавить метод _add_stars(1) в CharacterController)
    hero.model.stars = getattr(hero.model, 'stars', 0) + 1
    await hero.save_all()

    await callback.message.edit_text(callback.message.html_text + "\n\n<i>✅ Выполнено! Получена 1 🌟</i>",
                                     parse_mode="HTML")
    await callback.answer("Выполнено! +1 Звездочка", show_alert=True)