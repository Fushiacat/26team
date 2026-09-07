import pytest
from src.db import create_user, get_user, update_user, delete_user, get_all_users, get_users_by_role


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


@pytest.mark.asyncio
async def test_delete_user():
    await create_user(801, "Удаляемый", "09.03.01", "seeker")
    deleted = await delete_user(801)
    assert deleted is True
    user = await get_user(801)
    assert user is None


@pytest.mark.asyncio
async def test_delete_user_not_found():
    deleted = await delete_user(999999)
    assert deleted is False


@pytest.mark.asyncio
async def test_create_user_with_desired_role_and_about():
    user = await create_user(
        telegram_id=501,
        name="Полный",
        direction="09.03.04",
        role="seeker",
        desired_role="dev",
        about_text="Python dev, 3 года опыта",
    )
    assert user["desired_role"] == "dev"
    assert user["about_text"] == "Python dev, 3 года опыта"


@pytest.mark.asyncio
async def test_create_user_without_optional_fields():
    user = await create_user(
        telegram_id=502,
        name="Минимальный",
        direction="09.03.01",
        role="organizer",
    )
    assert user["desired_role"] is None
    assert user["about_text"] is None


@pytest.mark.asyncio
async def test_update_user_about_text():
    await create_user(503, "Оảnновой", "09.03.03", "seeker")
    await update_user(503, about_text="Новый текст о себе")
    user = await get_user(503)
    assert user["about_text"] == "Новый текст о себе"


@pytest.mark.asyncio
async def test_update_user_clear_about_text():
    await create_user(504, "Чистый", "09.03.01", "seeker", about_text="Был текст")
    await update_user(504, about_text=None)
    user = await get_user(504)
    assert user["about_text"] is None


@pytest.mark.asyncio
async def test_update_user_desired_role():
    await create_user(505, "Роль", "09.03.04", "seeker", desired_role="ba")
    await update_user(505, desired_role="sa")
    user = await get_user(505)
    assert user["desired_role"] == "sa"


@pytest.mark.asyncio
async def test_update_user_role_clears_optional():
    await create_user(506, "Смена", "09.03.01", "seeker", desired_role="dev", about_text="текст")
    await update_user(506, role="organizer", direction=None, desired_role=None, about_text=None)
    user = await get_user(506)
    assert user["role"] == "organizer"
    assert user["direction"] is None
    assert user["desired_role"] is None
    assert user["about_text"] is None
