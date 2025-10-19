from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo, \
    InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from common import keyboards
from common.models import User, Anketa
from common.keyboards import reactions_kb
import config

class AnketaRouter:
    def __init__(self, bot):
        self.bot = bot
        self.router = Router()
        self.router.message.register(self._anketka, F.text.in_(["📄 Профиль"]))
        self.router.message.register(self._random_anketa, F.text == "➕ Прислать новые анкеты")
        self.router.callback_query.register(self._handle_reaction, F.data.startswith("reaction_"))
        self.router.message.register(self._show_likes, F.text == "👍 Взаимные лайки")

    async def _show_likes(self, msg: Message):
        user = User.get(msg.from_user.id)
        if not user:
            return await msg.answer("ты не зареґаний...")

        ank = Anketa(user)
        mliked = ank.get_mutual_likes()

        text = "<b>💙 Вот твои взаимные лайки:</b>\n"
        if mliked:
            for u in mliked[-10:]:
                text += f"• {u.name} (@{(await self.bot.get_chat(u.tg_id)).username or 'нетюзера'})\n"
        else:
            text += "а их нету 🤷\n"

        await msg.answer(text, parse_mode="HTML", reply_markup=keyboards.main_kb)

    async def send_anketa(self, chat, user: User, show_reactions=True, show_username=False, mutual=False):
        # chat может быть int (chat_id) или Message
        media_ids = user.media or []

        loc = (
            f"{''.join([chr(0x1F1E6 + ord(c.upper()) - ord('A')) for c in (user.geo.country_code or '')[:2]]) or '🌍'} {user.geo.country}, {user.geo.city}"
            if user.geo.city else "🌍 ?"
        )

        try:
            user_obj = await self.bot.get_chat(user.tg_id)
            username = user_obj.username if mutual and user_obj.username else None
            uname = f" (@{username})" if username else ""
        except TelegramBadRequest:
            uname = ""

        us = "Общение или Отношения" if len(user.filters.ftype) >= 2 else user.filters.ftype[0].value
        text = (
            f"👤 <b>{user.name}</b>{uname}\n"
            f"➡️ <b>Ищет</b> {us}\n\n"
            f"📍 <b>Локация:</b> {loc}\n"
            f"📅 <b>Возраст:</b> {user.age}\n"
            f"⚧ <b>Пол:</b> {user.sex.value}\n"
            f"⚧ <b>Ориентация:</b> {user.orientation.value}\n"
            f"🎨 <b>Хобби:</b> {', '.join(user.hobby) if user.hobby else 'Не указаны'}\n"
            f"💬 <b>О себе:</b>\n{user.bio or 'Не указано'}"
        )

        reply_to = None
        if media_ids:
            album = []
            for fid in media_ids[:10]:
                if not fid.startswith("BAAC"):
                    album.append(InputMediaPhoto(media=fid))
                else:
                    album.append(InputMediaVideo(media=fid))
            if isinstance(chat, (int, str)):  # chat_id
                sent = await self.bot.send_media_group(chat_id=chat, media=album)
                reply_to = sent[0].message_id
            else:
                sent = await chat.answer_media_group(album)
                reply_to = sent[0].message_id

        if isinstance(chat, (int, str)):
            await self.bot.send_message(
                chat_id=chat,
                text=text,
                reply_markup=reactions_kb(user.tg_id) if show_reactions else None,
                parse_mode="HTML",
                reply_to_message_id=reply_to,
            )
        else:
            await chat.answer(
                text,
                reply_markup=reactions_kb(user.tg_id) if show_reactions else None,
                parse_mode="HTML",
                reply_to_message_id=reply_to,
            )

    async def _handle_reaction(self, callback: CallbackQuery):
        action, user_id_str = callback.data.split(":")
        to_id = int(user_id_str)
        from_id = callback.from_user.id

        if to_id == from_id:
            await callback.answer("Это ты сам, не лайкай себя! 🤡", show_alert=True)
            return

        user_to = User.get(to_id)
        user_from = User.get(from_id)
        if not user_to or not user_from:
            await callback.answer("Анкета недоступна или ты не зарегистрирован", show_alert=True)
            return

        anketa_to = Anketa(user_to)
        anketa_from = Anketa(user_from)

        if action == "reaction_like":
            liked_first_time = anketa_to.add_like(from_id)

            mutual = Anketa.is_mutual_like(from_id, to_id)
            if mutual:
                await callback.answer("У вас взаимный лайк! 🎉")
                try:
                    username_from = (await self.bot.get_chat(from_id)).username or ""
                    username_to = (await self.bot.get_chat(to_id)).username or ""
                    if username_from:
                        await self.bot.send_message(
                            from_id,
                            f"У вас взаимный лайк с @{username_to}! Начинайте общаться 😉"
                        )
                    if username_to:
                        await self.bot.send_message(
                            to_id,
                            f"У вас взаимный лайк с @{username_from}! Начинайте общаться 😉"
                        )
                except TelegramBadRequest:
                    pass

                # отправляем анкеты обоим напрямую в их чаты (chat_id)
                await self.send_anketa(from_id, user_to, show_reactions=False, show_username=True, mutual=True)
                await self.send_anketa(to_id, user_from, show_reactions=False, show_username=True, mutual=True)
                return
            else:
                await callback.answer("Лайк поставлен!")
                try:
                    await self.bot.send_message(
                        to_id,
                        f"Тебя лайкнул {user_from.name}! Можешь ответить и сделать взаимный лайк."
                    )
                    # отправляем анкету лайкнувшего **в чат того, кого лайкнули**
                    await self.send_anketa(to_id, user_from, show_reactions=True, show_username=False, mutual=False)
                except TelegramBadRequest:
                    pass

            # показываем лайкнувшему новую анкету (ответом в чат, где коллбек)
            await self._send_next_anketa(callback.message, from_id, exclude_ids=[from_id, to_id])

        elif action == "reaction_dislike":
            await callback.answer("Пропущено")
            await self._send_next_anketa(callback.message, from_id, exclude_ids=[from_id, to_id])

    async def _send_anketa_by_id(self, message, user_id: int, show_user_id: int, mutual: bool):
        user = User.get(show_user_id)
        if not user:
            await message.answer("Анкета недоступна")
            return
        await self.send_anketa(message, user, show_reactions=True, show_username=mutual, mutual=mutual)

    async def _send_next_anketa(self, message_or_chat_id, user_id: int, exclude_ids=None):
        exclude_ids = exclude_ids or []
        user = User.get(user_id)
        if not user:
            if isinstance(message_or_chat_id, (int, str)):
                await self.bot.send_message(message_or_chat_id, "Ты не зарегистрирован!")
            else:
                await message_or_chat_id.answer("Ты не зарегистрирован!")
            return

        ankets = Anketa.search(filters=user.filters, exclude_ids=exclude_ids, limit=1)
        if not ankets:
            if isinstance(message_or_chat_id, (int, str)):
                await self.bot.send_message(message_or_chat_id, "Никого не нашлось... Попробуй позже!")
            else:
                await message_or_chat_id.answer("Никого не нашлось... Попробуй позже!")
            return

        found = ankets[0]
        await self.send_anketa(message_or_chat_id, found.owner_user, show_reactions=True, show_username=False, mutual=False)

    async def _anketka(self, msg: Message):
        user = User.get(msg.from_user.id)
        if not user:
            return await msg.answer("Ты не зарегистрирован...")
        await self.send_anketa(msg, user, show_reactions=False, show_username=True, mutual=False)

    async def _random_anketa(self, msg: Message):
        user = User.get(msg.from_user.id)
        if not user:
            return await msg.answer("Ты не зарегистрирован...")

        exclude_ids = [user.tg_id]
        ankets = Anketa.search(filters=user.filters, exclude_ids=exclude_ids, limit=1)

        if not ankets:
            await msg.answer("Никого не нашлось... Попробуй позже!")
            return

        found = ankets[0]
        await self.send_anketa(msg, found.owner_user, show_reactions=True, show_username=False, mutual=False)
