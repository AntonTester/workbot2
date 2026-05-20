from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.texts import Texts
from bot.keyboards import Keyboards
from bot.states import ContractForm

from db.database import Database
from db.contract_repo import ContractRepo
from core.character_controller import CharacterController

router = Router()

# Для Доски Контрактов создаем отдельный репозиторий
db_instance = Database("oskolki.db")
contract_repo = ContractRepo(db_instance)

# === 1. Просмотр Доски ===
@router.message(F.text == Texts.BTN_CONTRACTS)
async def show_board(message: Message):
    contracts = contract_repo.get_active_contracts(message.from_user.id)

    await message.answer(
        text=Texts.board_sheet(contracts),
        reply_markup=Keyboards.board_menu(contracts),
        parse_mode="HTML"
    )

# === 2. ВЫПОЛНЕНИЕ КОНТРАКТА ===
@router.callback_query(F.data.startswith("complete_"))
async def execute_contract(call: CallbackQuery, hero: CharacterController):
    await call.answer("Оформляем документы...")

    contract_id = int(call.data.split("_")[1])

    # Получаем контракт и проверяем его актуальность
    contract = contract_repo.get_contract(contract_id)
    if not contract or contract["status"] != "active":
        await call.message.answer("❌ <i>Этот контракт уже закрыт или не существует.</i>", parse_mode="HTML")
        return

    # Герой сам рассчитывает кубики, лут, опыт и золото, сохраняя это в БД
    result = await hero.complete_contract(contract["difficulty"], contract["duration"])

    # Помечаем контракт как выполненный в базе задач
    contract_repo.close_contract(contract_id)

    # Удаляем меню с выполненным контрактом из старого сообщения
    await call.message.edit_reply_markup(reply_markup=None)

    # Отправляем красивый отчет о выполнении
    await call.message.answer(
        text=Texts.contract_completed(contract["name"], result),
        parse_mode="HTML"
    )

    # Выводим обновленную доску
    contracts = contract_repo.get_active_contracts(call.from_user.id)
    await call.message.answer(
        text=Texts.board_sheet(contracts),
        reply_markup=Keyboards.board_menu(contracts),
        parse_mode="HTML"
    )

# === 3. Запуск создания контракта ===
@router.callback_query(F.data == "start_contract")
async def start_contract_creation(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(ContractForm.drafting)
    await state.update_data(diff_idx=0, dur_idx=0, day_idx=0)

    await call.message.answer(
        text=Texts.CONTRACT_DRAFT_PROMPT,
        reply_markup=Keyboards.contract_draft_kb(0, 0, 0),
        parse_mode="HTML"
    )

# === 4. Обработка переключателей (inline кнопок) ===
@router.callback_query(ContractForm.drafting, F.data.startswith("toggle_"))
async def process_toggles(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    action = call.data.split("_")[1]

    if action == "diff":
        data["diff_idx"] = (data["diff_idx"] + 1) % len(Texts.DIFFICULTIES)
    elif action == "dur":
        data["dur_idx"] = (data["dur_idx"] + 1) % len(Texts.DURATIONS)
    elif action == "day":
        data["day_idx"] = (data["day_idx"] + 1) % len(Texts.get_deadline_options())

    await state.update_data(**data)
    await call.message.edit_reply_markup(
        reply_markup=Keyboards.contract_draft_kb(data["diff_idx"], data["dur_idx"], data["day_idx"])
    )

# === 5. Отмена создания ===
@router.callback_query(ContractForm.drafting, F.data == "cancel_contract")
async def cancel_creation(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(Texts.CONTRACT_CANCELED, parse_mode="HTML")

# === 6. Завершение создания (ввод названия текстом) ===
@router.message(ContractForm.drafting, F.text)
async def finalize_contract(message: Message, state: FSMContext):
    data = await state.get_data()

    difficulty = Texts.DIFFICULTIES[data["diff_idx"]]
    duration = Texts.DURATIONS[data["dur_idx"]]
    deadline = Texts.get_deadline_options()[data["day_idx"]]
    contract_name = message.text

    # Сохраняем в БД задач
    contract_repo.add_contract(message.from_user.id, contract_name, difficulty, duration, deadline)
    await state.clear()

    await message.answer(Texts.CONTRACT_ADDED, parse_mode="HTML")

    # Сразу показываем обновленную доску
    contracts = contract_repo.get_active_contracts(message.from_user.id)
    await message.answer(
        text=Texts.board_sheet(contracts),
        reply_markup=Keyboards.board_menu(contracts),
        parse_mode="HTML"
    )