from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from common.models import User, Gender, Hobby, Orientation, Filters, Geo, FType
from common.keyboards import settings_kb, back_kb, gender_kb, fgender_kb, orientation_kb, s_kb
from utils.geo import validate_city
from common.states import Settings
import time
import re

router = Router()

def filters_hobby_kb(selected=None):
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

# старт настроек - меню выбора
@router.message(lambda m: m.text == "⚙️ Настройки")
async def settings_start(msg: Message, state: FSMContext):
    user = User.get(tg_id=msg.from_user.id)
    if not user:
        await msg.answer("Ты не зарегистрирован. Напиши /start чтобы зарегистрироваться.")
        return
    await msg.answer("Что хочешь изменить?", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)


# обработка выбора из меню настроек
@router.message(Settings.choosing_action)
async def settings_choice(msg: Message, state: FSMContext):
    text = msg.text

    if text == "📷 Изменить фото/видео":
        data = await state.get_data()
        media = data.get("media", None)
        if media is None:
            media = []
            await state.update_data(media=media)
        await msg.answer(
            f"Пришли до 4 своих фото/видео и нажми ✅ Готово (ТОЛЬКО БЫСТРОЙ ОТПРАВКОЙ)",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="✅ Готово"), KeyboardButton(text="🔙 Назад")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        await state.set_state(Settings.editing_media)

    elif text == "📑 Изменить текст анкеты":
        await msg.answer("Напиши новое био", reply_markup=back_kb)
        await state.set_state(Settings.editing_bio)

    elif text == "🧪 Изменить фильтры":
        await msg.answer("Выбери что менять:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Возраст"), KeyboardButton(text="Пол")],
                [KeyboardButton(text="Хобби"), KeyboardButton(text="Цели")],
                [KeyboardButton(text="🔙 Назад")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        ))
        await state.set_state(Settings.choosing_action)  # оставим в том же, чтоб ловить подменю

    elif text == "🔞 Изменить возвраст":
        await msg.answer("Введи новый возраст", reply_markup=back_kb)
        await state.set_state(Settings.editing_age)

    elif text == "❌ Зарегистрироваться заново (Статистика и лайки останутся)":
        await msg.answer(
            'Если точно хочешь удалить аккаунт — напиши слово "удалить".\nДля отмены — напиши что угодно другое.',
            reply_markup=back_kb)
        await state.set_state(Settings.awaiting_delete_confirm_text)

    elif text == "Возраст":
        await msg.answer("Введи возрастной фильтр (например 18-25)", reply_markup=back_kb)
        await state.set_state(Settings.editing_filters_age)

    elif text == "Пол":
        await msg.answer("Выбери пол для фильтра", reply_markup=fgender_kb)
        await state.set_state(Settings.editing_filters_sex)

    elif text == "Хобби":
        await msg.answer("Выбери свои хобби кнопочками (можно несколько), потом нажми ✅ Готово",
                         reply_markup=hobby_kb())
        await state.set_state(Settings.editing_filters_hobby)
        await state.update_data(hobby=[])

    elif text == "Цели":
        await msg.answer("Выбери цели фильтра", reply_markup=s_kb)
        await state.set_state(Settings.editing_filters_ftype)

    elif text == "🔙 Назад":
        await msg.answer("Возвращаю в главное меню", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)

    else:
        await msg.answer("Не понимаю, выбери пункт с клавиатуры")

@router.message(Settings.awaiting_delete_confirm_text)
async def process_delete_confirmation(msg: Message, state: FSMContext):
    if msg.text.lower() == "удалить":
        user = User.get(tg_id=msg.from_user.id)
        if user:
            user.delete()
        await msg.answer("Аккаунт удалён. Напиши /start, чтобы зарегистрироваться заново.", reply_markup=None)
        await state.clear()
    else:
        await msg.answer("Удаление отменено.", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)

# изменение возраста
@router.message(Settings.editing_age)
async def edit_age(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return
    try:
        age = int(msg.text.strip())
        if not (9 <= age <= 99):
            raise ValueError()
    except:
        await msg.answer("Неверный возраст, попробуй ещё раз")
        return

    User.get(tg_id=msg.from_user.id).update(age=age)
    await msg.answer(f"Возраст обновлен: {age}", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# изменение био
@router.message(Settings.editing_bio)
async def edit_bio(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return
    bio = msg.text.strip()

    if len(bio) > 1500:
        await msg.answer("Биография не может быть длиннее 1500 символов, напиши ещё раз")
        return

    if not re.fullmatch(r"^[^<>\/\\]+$", bio):
        await msg.answer("Био не может содержать символы: < > / \\")
        return

    User.get(tg_id=msg.from_user.id).update(bio=bio)
    await msg.answer("Био обновлено", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# изменение пола
@router.message(Settings.editing_gender)
async def edit_gender(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return
    sex_value = msg.text.strip()
    gender = next((g for g in Gender if g.value == sex_value), None)
    if gender is None:
        await msg.answer("Неверный пол. Выбери его на клавиатуре")
        return
    User.get(tg_id=msg.from_user.id).update(sex=gender.value)
    await msg.answer(f"Пол обновлен: {gender.value}", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# изменение города
@router.message(Settings.editing_city)
async def edit_city(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    geo = validate_city(msg.text)
    if geo is None:
        await msg.answer("Город не найден, попробуй ещё раз")
        return

    User.get(tg_id=msg.from_user.id).update(geo=geo.dict())
    await msg.answer(f"Город обновлен: {geo.city}", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# изменение хобби
@router.message(Settings.editing_hobby)
async def edit_hobby(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    if msg.text == "✅ Готово":
        data = await state.get_data()
        if not data.get("hobby") or data.get("hobby") == []:
            await msg.answer("Ты не выбрал ни одного хобби 😭")
            return
        current = data.get("hobby", [])
        User.get(tg_id=msg.from_user.id).update(hobby=current)
        return

    hobby_value = msg.text
    data = await state.get_data()
    current = data.get("hobby", [])

    hobby = next((h for h in Hobby if h.value == re.sub(r"^(✅\s*)+", "", msg.text).strip()), None)
    if not hobby:
        await msg.answer("Выбери хобби на клавиатуре", reply_markup=hobby_kb(current))
        return

    if hobby_value in current:
        current.remove(hobby_value)
    else:
        current.append(hobby_value)

    await state.update_data(hobby=current)
    await msg.answer("Хобби обновлены", reply_markup=hobby_kb(current))

# изменение ориентации
@router.message(Settings.editing_orientation)
async def edit_orientation(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return
    ori = msg.text.strip()
    if ori not in [o.value for o in Orientation]:
        await msg.answer("Неверная ориентация, выбери её на клавиатуре")
        return
    User.get(tg_id=msg.from_user.id).update(orientation=ori)
    await msg.answer(f"Ориентация обновлена: {ori}", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# медиа (фото/видео) загрузка
@router.message(Settings.editing_media, F.content_type.in_(["photo", "video"]))
async def media_upload(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    data = await state.get_data()
    media = data.get("media", [])
    if len(media) >= 4:
        await msg.answer("Уже есть 4 медиа, жми ✅ Готово (после нажатия можно будет изменить)")
        return
    fid = msg.photo[-1].file_id if msg.photo else msg.video.file_id
    media.append(fid)
    await state.update_data(media=media)
    await msg.answer(f"Получил ваше медиа, можно ещё {4 - len(media)}")

@router.message(Settings.editing_media, F.text == "✅ Готово")
async def media_done(msg: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    User.get(tg_id=msg.from_user.id).update(media=media)
    await msg.answer("Фото/видео обновлены", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

@router.message(Settings.editing_media, F.text == "🔙 Назад")
async def media_back(msg: Message, state: FSMContext):
    await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# фильтр возраст
@router.message(Settings.editing_filters_age)
async def edit_filters_age(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    try:
        from_age, to_age = msg.text.strip().split("-")
        from_age, to_age = int(from_age), int(to_age)
        if from_age > to_age or from_age < 9:
            raise ValueError()
    except:
        await msg.answer("Возраст должен быть радиусом (например 18-25), попробуй ещё раз")
        return

    user = User.get(tg_id=msg.from_user.id)
    filters = user.filters
    filters.age_from = from_age
    filters.age_to = to_age
    user.update(filters=filters.model_dump())
    await msg.answer(f"Фильтр возраста обновлен: {from_age}-{to_age}", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# фильтр пол
@router.message(Settings.editing_filters_sex)
async def edit_filters_sex(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    sex_value = msg.text.strip()
    if sex_value != "Не важно":
        gender = next((g for g in Gender if g.value == sex_value), None)
        if gender is None:
            await msg.answer("Неверный пол. Выбери его на клавиатуре")
            return
        sex_value = [gender]
    else:
        sex_value = [Gender.male, Gender.female, Gender.other]

    user = User.get(tg_id=msg.from_user.id)
    filters = user.filters
    filters.sex = sex_value
    user.update(filters=filters.model_dump())
    await msg.answer(f"Фильтр пола обновлен: {', '.join([g.value for g in sex_value])}", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)

# фильтр хобби
@router.message(Settings.editing_filters_hobby)
async def edit_filters_hobby(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    data = await state.get_data()
    current = data.get("filters_hobby", [])

    if msg.text == "✅ Готово":
        if not data.get("filters_hobby") or data.get("filters_hobby") == []:
            await msg.answer("Ты не выбрал ни одного хобби 😭")
            return
        user = User.get(tg_id=msg.from_user.id)
        filters = user.filters
        filters.hobby = current
        user.update(filters=filters.model_dump())

        await msg.answer("Фильтр хобби обновлён", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    hobby = next((h for h in Hobby if h.value == re.sub(r"^(✅\s*)+", "", msg.text).strip()), None)
    if not hobby:
        await msg.answer("Выбери хобби на клавиатуре", reply_markup=hobby_kb(current))
        return

    if hobby in current:
        current.remove(hobby)
    else:
        current.append(hobby)

    await state.update_data(filters_hobby=current)
    await msg.answer("Хобби обновлено", reply_markup=filters_hobby_kb(current))


# фильтр цели
@router.message(Settings.editing_filters_ftype)
async def edit_filters_ftype(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Возвращаю в настройки", reply_markup=settings_kb)
        await state.set_state(Settings.choosing_action)
        return

    text = msg.text.strip().lower()

    if text == "что угодно":
        selected_ftypes = [FType.basic, FType.romantic]
    elif text == "общение":
        selected_ftypes = [FType.basic]
    elif text == "отношения":
        selected_ftypes = [FType.romantic]
    else:
        await msg.answer("Выбери один из вариантов на клавиатуре", reply_markup=s_kb)
        return

    user = User.get(tg_id=msg.from_user.id)
    filters = user.filters
    filters.ftype = selected_ftypes
    user.update(filters=filters.model_dump())

    await msg.answer(f"Фильтр целей обновлен: {', '.join([f.value for f in selected_ftypes])}", reply_markup=settings_kb)
    await state.set_state(Settings.choosing_action)
