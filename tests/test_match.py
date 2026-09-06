import pytest
from src.db import create_user, get_users_by_role


@pytest.mark.asyncio
async def test_match_seeker_finds_organizer():
    await create_user(501, "Организатор", "09.03.01", "organizer")
    await create_user(502, "Искатель", "09.03.03", "seeker")
    organizers = await get_users_by_role("organizer")
    assert len(organizers) == 1
    assert organizers[0]["telegram_id"] == 501


@pytest.mark.asyncio
async def test_match_organizer_finds_seeker():
    await create_user(601, "Искатель", "09.03.01", "seeker")
    await create_user(602, "Организатор", "09.03.03", "organizer")
    seekers = await get_users_by_role("seeker")
    assert len(seekers) == 1
    assert seekers[0]["telegram_id"] == 601


@pytest.mark.asyncio
async def test_match_no_duplicates():
    await create_user(701, "Один", "09.03.01", "seeker")
    all_users = await get_users_by_role("organizer")
    assert len(all_users) == 0
