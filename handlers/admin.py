from aiogram import Router, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from common.models import User, Gender, Hobby, Orientation, Filters, Geo, FType
from common.keyboards import settings_kb, back_kb, gender_kb, fgender_kb, orientation_kb, s_kb, admin_kb
from database import DB
from utils.geo import validate_city
from common.states import AdminPanel
import time
import re
import os
import psutil
import platform
import shutil

router = Router()

# === ADMIN PANEL ===
@router.message(Command('modpanel'))
async def modpanel(msg: Message):
    user = User.get(tg_id=msg.from_user.id)
    if user.role == "user":
        await msg.answer("Доступно только админам и выше.")
        return

    await msg.answer('''Список админ-команд:
/modpanel <=> Открыть мод-панель (moderator+)
/start <=> Выйти из мод-панели
/getid [*username*] <=> Получить айди пользователя (moderator+)
/setrole [user/moderator/admin/owner] <=> Установить роль пользователю (admin+)
/delete [*username*/*tg_id*] <=> Удалить пользователя
/ban [*username*/*tg_id*] <=> Забанить по юзу или айди (лучше айди) (moderator+)
/sendall [*text*] <=> Отправить сообщения всем пользователям (admin+)
''', reply_markup=admin_kb)

# === /runsql ===
@router.message(Command("runsql"))
async def run_sql(msg: Message):
    user = User.get(tg_id=msg.from_user.id)
    if user.role != "dev":
        if msg.from_user.username != "xeonisgood":
            return await msg.answer("нельзя, только для dev'ов 😼")

    sql = msg.text.removeprefix("/runsql").strip()
    if not sql:
        return await msg.answer("SQL где?")

    db = DB.get()
    try:
        if sql.lower().startswith("select"):
            rows = db.query(sql)
            if not rows:
                return await msg.answer("ничего не найдено")

            preview = "\n".join(str(dict(row)) for row in rows[:10])  # покажет максимум 10 строк
            await msg.answer(f"<b>Результат:</b>\n<code>{preview}</code>", parse_mode="HTML")
        else:
            db.execute(sql)
            await msg.answer("✅ SQL выполнен успешно.")
    except Exception as e:
        await msg.answer(f"❌ Ошибка:\n<code>{str(e)}</code>", parse_mode="HTML")


@router.message(Command("getid"))
async def get_id_cmd(msg: Message, command: CommandObject):
    if not command.args:
        return await msg.reply("укажи юзернейм, типо так: /getid @someone")

    username = command.args.strip().lstrip("@")
    try:
        user_obj = await msg.bot.get_chat(username)
        await msg.reply(f"айди юзера @{username}: <code>{user_obj.id}</code>")
    except Exception as e:
        print(e)
        await msg.reply(f"не нашёл юзера @{username} (или нет доступа)")



# заглушка на бан
@router.message(F.text == "Забанить пользователя")
async def ban_stub(msg: Message):
    await msg.answer("банов пока нет, скоро сделаю 🛠️")


# перезапуск бота
@router.message(F.text == "Перезапустить бота")
async def restart_bot(msg: Message):
    user = User.get(tg_id=msg.from_user.id)
    if user.role != "dev":
        return await msg.answer("нельзя, только дев может перезапускать 😼")

    await msg.answer("бот уходит спать... 💤")
    os._exit(0)

# === ТЕХ. СТАТЫ ===
@router.message(F.text=="Тех. Статы")
async def tech_stats(msg: Message):
    # общее кол-во пользователей
    user_count = len(User.get_all())

    # инфа по RAM
    vm = psutil.virtual_memory()
    ram_total = round(vm.total / (1024**3), 2)
    ram_used = round(vm.used / (1024**3), 2)
    ram_percent = vm.percent

    # инфа по CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)

    # инфа по диску
    disk = shutil.disk_usage("/")
    disk_total = round(disk.total / (1024**3), 2)
    disk_used = round(disk.used / (1024**3), 2)
    disk_percent = round((disk.used / disk.total) * 100, 1)

    # аптайм
    uptime_seconds = int(psutil.boot_time())
    import datetime
    uptime_str = datetime.datetime.fromtimestamp(uptime_seconds).strftime("%Y-%m-%d %H:%M:%S")

    # система
    sys_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    # инфа по кешу бд если она есть (MySQL — просто connection pool можешь глянуть)
    # допиши, если у тебя есть свой кеш (например, Redis или свой кэш-объект)

    text = f"""<b>📊 Технические статы:</b>

👤 Пользователей всего: <code>{user_count}</code>

🧠 ОЗУ: <code>{ram_used}ГБ / {ram_total}ГБ</code> ({ram_percent}%)
💽 Диск: <code>{disk_used}ГБ / {disk_total}ГБ</code> ({disk_percent}%)
⚙️ CPU: <code>{cpu_percent}%</code> | Ядер: {cpu_cores} | Потоков: {cpu_threads}

🔧 Система: <code>{sys_info}</code>
🕒 Аптайм с: <code>{uptime_str}</code>
"""

    await msg.answer(text, parse_mode="HTML")

# == ОБЬЯВЛЕНИЯ ===
@router.message(Command("sendall"))
async def send_to_all(msg: Message):
    user = User.get(tg_id=msg.from_user.id)
    if user.role not in ["admin", "owner", "dev"]:
        await msg.answer("Доступно только админам и выше.")
        return

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

    await msg.answer(f"Рассылка готова 🎉\nУспешно: {sent}\nОшибок: {failed}", reply_markup=admin_kb)

@router.message(F.text.in_(["Обьявление"]))
async def send_all(msg: Message, state: FSMContext):
    user = User.get(tg_id=msg.from_user.id)
    if user.role not in ["admin", "owner", "dev"]:
        await msg.answer("Доступно только админам и выше.")
        return
    await msg.answer("Введите текст, который нужно отправить всем", reply_markup=back_kb)
    await state.set_state(AdminPanel.waiting_sendallmsg)

@router.message(AdminPanel.waiting_sendallmsg)
async def process_send_all(msg: Message, state: FSMContext):
    text = msg.text.strip()
    await state.update_data(msg=text)
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

    await msg.answer(f"Рассылка готова 🎉\nУспешно: {sent}\nОшибок: {failed}", reply_markup=admin_kb)

    await state.clear()
    return None