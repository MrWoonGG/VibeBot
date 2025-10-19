from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from common.models import User, Anketa

stats_router = Router()

# обработчик кнопки 📊 Статистика
@stats_router.message(F.text.in_(["📊 Статистика"]))
async def show_stats(msg: Message):
    user = User.get(msg.from_user.id)
    if not user:
        await msg.answer("Ты не зарегистрирован...")
        return

    anketa = Anketa(user)
    total_likes = anketa.total_likes()
    mutual_likes = anketa.total_mutual_likes()
    liked_you = anketa.get_liked_you()  # список тех, кто лайкнул тебя
    you_liked = anketa.get_you_liked()  # список кого ты лайкнул

    text = (
        f"📊 <b>Твоя статистика:</b>\n"
        f"❤ Всего лайков: {str(total_likes)}\n"
        f"🎉 Получено лайков: {len(liked_you)}\n"
        f"👍 Ты лайкнул: {len(you_liked)}\n"
        f"💙 Взаимных лайков: {mutual_likes}"
    )
    await msg.answer(text, parse_mode="HTML")