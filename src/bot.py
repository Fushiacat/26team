from aiogram import Bot, Dispatcher
from src.config import BOT_TOKEN
from src.handlers.start import router as start_router
from src.handlers.profile import router as profile_router
from src.handlers.match import router as match_router

dp = Dispatcher()
dp.include_router(start_router)
dp.include_router(profile_router)
dp.include_router(match_router)


def create_bot() -> Bot:
    return Bot(token=BOT_TOKEN)
