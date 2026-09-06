import asyncio
from src.bot import create_bot, dp


async def main():
    bot = create_bot()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
