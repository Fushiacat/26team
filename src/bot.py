from aiogram import Bot, Dispatcher
from src.config import BOT_TOKEN
from src.handlers.start import router as start_router
from src.handlers.profile import router as profile_router
from src.handlers.match import router as match_router
from src.handlers.teams import router as teams_router
from src.db import init_db

dp = Dispatcher()
dp.include_router(start_router)
dp.include_router(profile_router)
dp.include_router(match_router)
dp.include_router(teams_router)


async def on_startup() -> None:
    await init_db()


dp.startup.register(on_startup)


def create_bot() -> Bot:
    return Bot(token=BOT_TOKEN)
