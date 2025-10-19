from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

gender_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")],
              [KeyboardButton(text="Другое"), KeyboardButton(text="🔙 Назад")]],
    one_time_keyboard=True,
    resize_keyboard=True
)

s_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Общение"), KeyboardButton(text="Отношения")],
        [KeyboardButton(text="Что угодно"), KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

filters_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👫 Пол", callback_data="filter_gender")],
        [InlineKeyboardButton(text="📍 Расстояние", callback_data="filter_distance")],
        [InlineKeyboardButton(text="📸 Только с фото", callback_data="filter_photo")],
        [InlineKeyboardButton(text="📂 Типы", callback_data="filter_types")],
        [InlineKeyboardButton(text="💞 Цели", callback_data="filter_purposes")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")],
    ]
)

del_confirm_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="no_del")],
        [InlineKeyboardButton(text="🗑️ Удалить аккаунт", callback_data="yes_del")],
    ]
)

fgender_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")],
              [KeyboardButton(text="Другое"), KeyboardButton(text="Не важно")],
              [KeyboardButton(text="🔙 Назад")]],
    one_time_keyboard=True,
    resize_keyboard=True
)

orientation_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Гетеросексуал")],
        [KeyboardButton(text="Биcексуал")],
        [KeyboardButton(text="Пансексуал")],
        [KeyboardButton(text="Гей")],
        [KeyboardButton(text="Лесби")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    one_time_keyboard=True,
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Профиль"),
        KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="👍 Взаимные лайки")],
        [KeyboardButton(text="➕ Прислать новые анкеты")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выбери действие...",
)

def reactions_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍", callback_data=f"reaction_like:{user_id}"),
            InlineKeyboardButton(text="👎", callback_data=f"reaction_dislike:{user_id}")
#            InlineKeyboardButton(text="Жалоба", callback_data=f"report:{user_id}")
        ]
    ])

admin_kb = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton(text="Узнать айди по юзу"), KeyboardButton(text="Обьявление")],
        [KeyboardButton(text="Удалить анкету"), KeyboardButton(text="Забанить пользователя")],
        [KeyboardButton(text="Жалобы"), KeyboardButton(text="Тех. Статы")],
        [KeyboardButton(text="Перезапустить бота")]
    ]
)

settings_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📷 Изменить фото/видео"),
         KeyboardButton(text="📑 Изменить текст анкеты")],
        [KeyboardButton(text="🧪 Изменить фильтры"),
        KeyboardButton(text="🔞 Изменить возвраст")],
        [KeyboardButton(text="❌ Зарегистрироваться заново (Статистика и лайки останутся)")],
        [KeyboardButton(text="🔙 В главное меню")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выбери действие...",
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)