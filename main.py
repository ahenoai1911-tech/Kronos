import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from core.config import settings
from db.database import init_db
from bot.handlers import start, tasks, planning, webapp_handler
from scheduler.jobs import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    await init_db()
    
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(planning.router)
    dp.include_router(webapp_handler.router)
    
    setup_scheduler(bot)
    
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
