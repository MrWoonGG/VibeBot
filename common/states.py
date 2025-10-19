from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class Settings(StatesGroup):
    choosing_action = State()
    awaiting_delete_confirm_text = State()
    editing_age = State()
    editing_gender = State()
    editing_city = State()
    editing_hobby = State()
    editing_orientation = State()
    editing_bio = State()
    editing_media = State()
    editing_filters_age = State()
    editing_filters_sex = State()
    editing_filters_hobby = State()
    editing_filters_ftype = State()

class AdminPanel(StatesGroup):
    waiting_sendallmsg = State()
    waiting_id = State()
    waiting_getid_username = State()
    waiting_delete_user = State()

class Registration(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_sex = State()
    waiting_city = State()
    waiting_hobby = State()
    waiting_orientation = State()
    waiting_bio = State()
    waiting_media = State()
    waiting_filters_age = State()
    waiting_filters_sex = State()
    waiting_filters_hobby = State()
    waiting_filters_ftype = State()
    waiting_hobby_button = State()
    finished = State()

class EditFiltersState(StatesGroup):
    menu = State()
    sex = State()
    age = State()
    ftype = State()
    hobby = State()
