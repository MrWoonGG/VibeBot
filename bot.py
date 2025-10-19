# VibeBot
# Code version: 1.0
# Made by MrWoon (https://kanokadev.top) for Selen

import asyncio
import logging
import config
import time
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Awaitable, Any
from handlers import start, ankets, settings, stats, admin
from handlers.ankets import AnketaRouter

# --- Врубим логгинг ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === АНТИСПАМ ===
class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, cooldown: float = 1.0):
        super().__init__()
        self.cooldown = cooldown
        self.user_timestamps: Dict[int, float] = {}
        self.user_media_count: Dict[int, int] = {}
        self.user_last_media_time: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()
        last_time = self.user_timestamps.get(user_id, 0)

        # проверка на медиа (фото, видео, доки, анимации и т.п.)
        is_media = any([
            event.photo,
            event.video,
            event.document,
            event.animation,
            event.video_note,
            event.voice
        ])

        if is_media:
            last_media_time = self.user_last_media_time.get(user_id, 0)
            media_count = self.user_media_count.get(user_id, 0)

            # если между медиа прошло больше секунды — сбросить счётчик
            if now - last_media_time > 1.5:
                media_count = 0

            media_count += 1
            self.user_media_count[user_id] = media_count
            self.user_last_media_time[user_id] = now

            if media_count <= 5:
                return await handler(event, data)  # разрешаем до 5 подряд

            # если >5 подряд — применяем кулдаун
            if now - last_time < self.cooldown:
                return await event.answer("медиа спамишь :< передохни чуть")

        else:
            # если это не медиа — сбрасываем медиа-счётчик
            self.user_media_count[user_id] = 0
            self.user_last_media_time[user_id] = 0

            if now - last_time < self.cooldown:
                return await event.answer("не так быстро, пж :<")

        self.user_timestamps[user_id] = now
        return await handler(event, data)

# === ФУНКЦИЯ ДЛЯ ЛЕВОГО ТЕКСТА ===
# @dp.message(F.text)
# async def unknown_command_handler(msg: Message):
#     if msg.text.startswith('/'): return
#     await msg.answer("Ничо не понял 😵‍💫\nНапиши /start чтоб открыть меню")

async def main():
    logger.info("Запуск бота...")

    # подключаем антиспам
    dp.message.middleware(AntiFloodMiddleware(cooldown=1.0))

    # подключаем роутеры
    dp.include_router(start.router)
    ankets = AnketaRouter(bot)
    dp.include_router(ankets.router)
    dp.include_router(settings.router)
    dp.include_router(stats.stats_router)
    dp.include_router(admin.router)
    logger.info("Роутеры подключены.")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
