import pytest
import asyncio
import aiosqlite
import os
from src.db import init_db, DB_PATH


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_test_db():
    os.makedirs("data", exist_ok=True)
    await init_db()
    yield
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users")
        await db.commit()
