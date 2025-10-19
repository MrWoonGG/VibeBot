from aiogram import Router, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command

import config
from common.states import Registration
import common.keyboards as keyboards
from aiogram.fsm.context  import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from common.models import User, Geo, Filters, Gender, Hobby, Orientation, Role, FType
from utils.geo import validate_city
import time
import re
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import DB

router = Router()

def hobby_filter_kb(selected=None):
    if selected is None:
        selected = []

    rows = []
    row = []

    for hobby in Hobby:
        text = f"✅ {hobby.value}" if hobby in selected else hobby.value
        row.append(KeyboardButton(text=text))
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([KeyboardButton(text="✅ Готово"), KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def hobby_kb(selected=None):
    if selected is None:
        selected = []

    rows = []
    row = []

    for hobby in Hobby:
        text = f"✅ {hobby.value}" if hobby.value in selected else hobby.value
        row.append(KeyboardButton(text=text))
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    # кнопки внизу
    rows.append([KeyboardButton(text="✅ Готово"), KeyboardButton(text="🔙 Назад")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@router.message(Command("sendall"))
async def send_to_all(msg: Message):
    if msg.from_user.username != "xeonisgood":
        return await msg.answer("нельзя, не дорос 😼")

    text = msg.text.removeprefix("/sendall").strip()
    if not text:
        return await msg.answer("а текст где?")

    users = User.get_all()
    sent, failed = 0, 0

    for user in users:
        try:
            await msg.bot.send_message(user.tg_id, text)
            sent += 1
        except TelegramAPIError:
            failed += 1

    await msg.answer(f"рассылка готова 🎉\nуспешно: {sent}\nошибок: {failed}")

# --- старт регистрации ---
@router.message(F.text.in_(["🔙 В главное меню", "/start"]))
async def cmd_register(msg: Message, state: FSMContext):
    await state.clear()
    user = User.get(tg_id=msg.from_user.id)
    if user:
        await msg.answer(f'''{config.BOT_NAME} v{config.BOT_VERSION}. Dev by @xeonisgood
Добро пожаловать, {user.name}!\nНажми на кнопку ➕ Прислать новые анкеты что-бы начать лайкать/дизлайкать анкеты и найти своих :)
''', reply_markup=keyboards.main_kb)
        if user.role in ["admin","owner","dev"]:
            await msg.answer(f"Мод-Панель доступна по команде /modpanel\n(Это сообщение видят только модераторы и выше)")
        return
    await msg.answer("Привет! Давай зарегистрируем тебя.\nКак тебя зовут?")
    await state.set_state(Registration.waiting_name)

# --- имя ---
@router.message(Registration.waiting_name)
async def process_name(msg: Message, state: FSMContext):
    name = msg.text.strip()

    if len(name) > 20:
        await msg.answer("Имя не может быть длиннее 20 символов")
        return

    if not re.fullmatch(r"[a-zA-Zа-яА-ЯёЁ]+", name):
        await msg.answer("Имя может содержать только буквы (a-z, а-я)")
        return

    await state.update_data(name=name)
    await msg.answer("Укажи свой возвраст", reply_markup=keyboards.back_kb)
    await state.set_state(Registration.waiting_age)

# --- дата рождения ---
@router.message(Registration.waiting_age)
async def process_age(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Введи своё имя", reply_markup=keyboards.back_kb)
        await state.set_state(Registration.waiting_name)
        return
    try:
        age = int(msg.text.strip())
        if not (9 <= age <= 99):
            raise ValueError()
    except:
        await msg.answer("Неверный возраст, попробуй ещё раз")
        return

    await state.update_data(age=age)
    await msg.answer("Выбери пол", reply_markup=keyboards.gender_kb)
    await state.set_state(Registration.waiting_sex)


# --- пол ---
@router.message(Registration.waiting_sex)
async def process_sex(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Введи свой возвраст", reply_markup=None)
        await state.set_state(Registration.waiting_age)
        return
    sex_value = msg.text.strip()
    gender = next((g for g in Gender if g.value == sex_value), None)
    if gender is None:
        await msg.answer("Неверный пол. Выбери его на клавиатуре")
        return
    await state.update_data(sex=sex_value)
    await msg.answer("Отлично! Теперь введи свой город (например, Киев)", reply_markup=keyboards.back_kb)
    await state.set_state(Registration.waiting_city)

# --- город ---
@router.message(Registration.waiting_city)
async def process_city(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Выбери пол", reply_markup=keyboards.gender_kb)
        await state.set_state(Registration.waiting_sex)
        return

    geo = validate_city(msg.text)
    if geo is None:
        await msg.answer("Город не найден, попробуй ещё раз")
        return

    await state.update_data(geo=geo)
    await msg.answer("Выбери свои хобби кнопочками (можно несколько), потом нажми ✅ Готово",
                     reply_markup=hobby_kb())
    await state.set_state(Registration.waiting_hobby_button)
    await state.update_data(hobby=[])


# --- хобби ---
@router.message(F.text, Registration.waiting_hobby_button)
async def hobby_toggle(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await state.set_state(Registration.waiting_city)
        await msg.answer("Ок, введи город ещё раз", reply_markup=keyboards.back_kb)
        return

    if msg.text == "✅ Готово":
        data = await state.get_data()
        if not data.get("hobby") or data.get("hobby") == []:
            await msg.answer("Ты не выбрал ни одного хобби 😭")
            return
        await state.set_state(Registration.waiting_orientation)
        await msg.answer("Теперь выбери ориентацию на клавиатуре", reply_markup=keyboards.orientation_kb)
        return

    hobby_value = re.sub(r"^(✅\s*)+", "", msg.text).strip()
    data = await state.get_data()
    current = data.get("hobby", [])

    hobby = next((h for h in Hobby if h.value == hobby_value), None)
    if not hobby:
        await msg.answer("Выбери хобби на клавиатуре", reply_markup=hobby_kb(current))
        return

    if hobby_value in current:
        current.remove(hobby_value)
    else:
        current.append(hobby_value)
    
    await state.update_data(hobby=current)
    await msg.answer("Хобби обновлены", reply_markup=hobby_kb(current))


# --- ориентация ---
@router.message(Registration.waiting_orientation)
async def process_orientation(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Выбери свои хобби кнопочками (можно несколько), потом нажми ✅ Готово",
                         reply_markup=hobby_kb())
        await state.set_state(Registration.waiting_hobby_button)
        await state.update_data(hobby=[])
        return
    ori = msg.text
    if ori not in [o.value for o in Orientation]:
        await msg.answer("Неверная ориентация, выбери её на клавиатуре")
        return
    await state.update_data(orientation=ori)
    await msg.answer("Расскажи немного о себе (био)", reply_markup=keyboards.back_kb)
    await state.set_state(Registration.waiting_bio)

# --- био ---
@router.message(Registration.waiting_bio)
async def process_bio(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("А какая ориентация?", reply_markup=keyboards.orientation_kb)
        await state.set_state(Registration.waiting_orientation)
        return
    bio = msg.text.strip()

    if len(bio) > 1500:
        await msg.answer("Биография не может быть длиннее 1500 символов")
        return

    if not re.fullmatch(r"^[^<>\/\\]+$", bio):
        await msg.answer("Био не может содержать символы: < > / \\")
        return

    await state.update_data(bio=bio)
    await msg.answer("Пришли до 4 своих фото/видео и нажми ✅ Готово (ТОЛЬКО БЫСТРОЙ ОТПРАВКОЙ)", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Готово"), KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    ))
    await state.set_state(Registration.waiting_media)

# Медиа
@router.message(Registration.waiting_media, F.content_type.in_(["photo","video"]))
async def media_upload(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Хорошо, расскажи немного о себе ещё раз")
        await state.set_state(Registration.waiting_bio)
        return
    data = await state.get_data()
    media = data.get("media", [])
    if len(media) >= 4:
        await msg.answer("Уже есть 4 медиа, жми ✅ Готово (после нажатия можно будет изменить)")
        return
    fid = msg.photo[-1].file_id if msg.photo else msg.video.file_id
    media.append(fid)
    await state.update_data(media=media)
    await msg.answer(f"Получил ваше медиа, можно ещё {4-len(media)}")

@router.message(Registration.waiting_media, F.text == "✅ Готово")
async def media_done(msg: Message, state: FSMContext):
    await msg.answer("Теперь, введи возраст людей в анкетах которые ты хочешь видеть в формате ОТ-ДО (например, 18-25)", reply_markup=keyboards.back_kb)
    await state.set_state(Registration.waiting_filters_age)

@router.message(Registration.waiting_media, F.text == "🔙 Назад")
async def media_back(msg: Message, state: FSMContext):
    await msg.answer("Расскажи немного о себе (био)", reply_markup=keyboards.back_kb)
    await state.set_state(Registration.waiting_bio)


# --- фильтр возраст ---
@router.message(Registration.waiting_filters_age)
async def process_filters_age(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Пришли до 4 своих фото/видео и нажми ✅ Готово (ТОЛЬКО БЫСТРОЙ ОТПРАВКОЙ)", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово"), KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True,
            one_time_keyboard=True
        ))
        await state.set_state(Registration.waiting_media)
        return

    try:
        from_age, to_age = msg.text.strip().split("-")
        from_age, to_age = [int(from_age), int(to_age)]
        if from_age > to_age or from_age < 9:
            raise ValueError()
    except:
        await msg.answer("Возраст должен быть радиусом (например 18-25), попробуй ещё раз")
        return

    await state.update_data(filters_age=msg.text.strip())
    await msg.answer("А кого ищешь?", reply_markup=keyboards.fgender_kb)
    await state.set_state(Registration.waiting_filters_sex)


# --- фильтр пол ---
@router.message(Registration.waiting_filters_sex)
async def process_filters_sex(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Введи возрастной фильтр (например 18-25)", reply_markup=keyboards.back_kb)
        await state.set_state(Registration.waiting_filters_age)
        return

    sex_value = msg.text.strip()
    if sex_value != "Не важно":
        gender = next((g for g in Gender if g.value == sex_value), None)
        if gender is None:
            await msg.answer("Неверный пол. Выбери его на клавиатуре")
            return
        sex_value = [sex_value]
    else:
        sex_value = ["Мужской", "Женский", "Другое"]

    await state.update_data(filters_sex=sex_value)
    await msg.answer("Выбери хобби для фильтра кнопочками (можно несколько), потом нажми ✅ Готово",
                     reply_markup=hobby_kb())
    await state.set_state(Registration.waiting_filters_hobby)
    await state.update_data(filters_hobby=[])


# --- фильтр хобби ---
@router.message(Registration.waiting_filters_hobby)
async def process_filters_hobby_buttons(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("А кого ищешь? (Мальчика/Девочку/Лампу)", reply_markup=keyboards.fgender_kb)
        await state.set_state(Registration.waiting_filters_sex)
        return

    if msg.text == "✅ Готово":
        data = await state.get_data()
        if not data.get("filters_hobby") or data.get('filters_hobby') == []:
            await msg.answer("Ты не выбрал ни одного хобби 😭")
            return
        await msg.answer("А что ты ищешь?", reply_markup=keyboards.s_kb)
        await state.set_state(Registration.waiting_filters_ftype)
        return

    hobby = next((h for h in Hobby if h.value == re.sub(r"^(✅\s*)+", "", msg.text).strip()), None)
    if not hobby:
        data = await state.get_data()
        selected = data.get("filters_hobby", [])
        await msg.answer("Выбери хобби из списка кнопками 😅", reply_markup=hobby_filter_kb(selected))
        return

    data = await state.get_data()
    selected = data.get("filters_hobby", [])

    if hobby in selected:
        selected.remove(hobby)
    else:
        selected.append(hobby)

    await state.update_data(filters_hobby=selected)
    await msg.answer("Хобби обновлены", reply_markup=hobby_filter_kb(selected))


# --- фильтр: что ищешь ---
@router.message(Registration.waiting_filters_ftype)
async def process_filters_ftype(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        AVAILABLE_HOBBIES = [hobby.value for hobby in Hobby]
        HOBBY_HINT = f"(Возможные: {', '.join(AVAILABLE_HOBBIES)})"
        await msg.answer("Выбери хобби для фильтра (через запятую).\n" + HOBBY_HINT, reply_markup=keyboards.back_kb)
        await state.set_state(Registration.waiting_filters_hobby)
        return

    text = msg.text.strip().lower()

    if text == "что угодно":
        selected_ftypes = ["Общение", "Отношения"]
    elif text == "общение":
        selected_ftypes = ["Общение"]
    elif text == "отношения":
        selected_ftypes = ["Отношения"]
    else:
        await msg.answer("Выбери один из вариантов на клавиатуре", reply_markup=keyboards.s_kb)
        return

    await state.update_data(filters_ftype=selected_ftypes)

    data = await state.get_data()

    sex_list = []
    for g in data["filters_sex"]:
        sex_list.append(Gender(g) if isinstance(g, str) else g)

    ftype_list = []
    for f in selected_ftypes:
        ftype_list.append(FType(f) if isinstance(f, str) else f)

    print(sex_list)
    print(ftype_list)
    filters = Filters(
        geo=Geo(**data["geo"]),
        age_from=int(data["filters_age"].split("-")[0]),
        age_to=int(data["filters_age"].split("-")[1]),
        sex=sex_list,
        hobby=data["filters_hobby"],
        ftype=ftype_list
    )

    await state.update_data(filters=filters.dict())

    User.create(
        tg_id=msg.from_user.id,
        role=Role.user,
        name=data["name"],
        geo=data["geo"],
        filters=filters.model_dump(),
        age=data["age"],
        sex=data["sex"],
        hobby=data["hobby"],
        bio=data["bio"],
        orientation=data["orientation"],
        media=data.get("media", []),
        registered_at=int(time.time())
    )

    await msg.answer("Регистрация завершена!\nНажми на кнопку ➕ Прислать новые анкеты что-бы начать лайкать/дизлайкать анкеты и найти своих :).", reply_markup=keyboards.main_kb)
    await state.clear()
