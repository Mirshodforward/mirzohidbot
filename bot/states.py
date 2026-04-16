from aiogram.fsm.state import State, StatesGroup


class AddStoreStates(StatesGroup):
    owner_phone = State()
    name = State()
    address = State()
    date_choice = State()
    manual_date = State()
    monthly_amount = State()
    electricity_kw = State()


class BroadcastStates(StatesGroup):
    text = State()


class UserToAdminStates(StatesGroup):
    message = State()


class EditStoreStates(StatesGroup):
    name = State()
    monthly = State()
    kw = State()
