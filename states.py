from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    wait_name = State()
    wait_birthday = State()
    wait_extra = State()


class CodeState(StatesGroup):
    waiting_for_code = State()


class BroadcastState(StatesGroup):
    waiting_for_recipients = State()
    waiting_for_message = State()