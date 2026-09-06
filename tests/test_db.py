import pytest
from src.db import create_user, get_user, update_user, get_all_users, get_users_by_role


@pytest.mark.asyncio
async def test_create_user():
    user = await create_user(
        telegram_id=123456,
        name="Тест",
        direction="09.03.01",
        role="seeker",
    )
    assert user is not None
    assert user["telegram_id"] == 123456
    assert user["name"] == "Тест"


@pytest.mark.asyncio
async def test_get_user():
    await create_user(111, "Алексей", "09.03.01", "seeker")
    user = await get_user(111)
    assert user is not None
    assert user["name"] == "Алексей"


@pytest.mark.asyncio
async def test_get_user_not_found():
    user = await get_user(999999)
    assert user is None


@pytest.mark.asyncio
async def test_update_user():
    await create_user(222, "Мария", "09.03.03", "organizer")
    await update_user(222, name="Мария Иванова")
    user = await get_user(222)
    assert user["name"] == "Мария Иванова"


@pytest.mark.asyncio
async def test_create_user_replace():
    await create_user(333, "Вася", "09.03.01", "seeker")
    await create_user(333, "Вася2", "09.03.03", "organizer")
    user = await get_user(333)
    assert user["name"] == "Вася2"
    assert user["role"] == "organizer"


@pytest.mark.asyncio
async def test_get_users_by_role():
    await create_user(441, "A", "09.03.01", "seeker")
    await create_user(442, "B", "09.03.01", "organizer")
    await create_user(443, "C", "09.03.01", "seeker")
    seekers = await get_users_by_role("seeker")
    assert len(seekers) == 2
    organizers = await get_users_by_role("organizer")
    assert len(organizers) == 1
