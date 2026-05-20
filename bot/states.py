from aiogram.fsm.state import State, StatesGroup

class ContractForm(StatesGroup):
    drafting = State() # Ожидание настройки параметров и ввода названия