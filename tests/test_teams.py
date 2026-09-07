import pytest
from src.db import (
    create_user, get_user, get_user_team, delete_user,
    create_team, get_team_by_number, get_team_by_id,
    add_team_member, remove_team_member, get_team_members, get_teams_by_creator,
    get_available_users_by_role, get_team_member, is_user_in_any_team,
)


@pytest.mark.asyncio
async def test_create_team():
    team = await create_team("A1", 1001)
    assert team is not None
    assert team["team_number"] == "A1"
    assert team["created_by"] == 1001


@pytest.mark.asyncio
async def test_create_team_duplicate():
    await create_team("B1", 1001)
    team = await create_team("B1", 1002)
    assert team is None


@pytest.mark.asyncio
async def test_get_team_by_number():
    await create_team("C1", 1001)
    team = await get_team_by_number("C1")
    assert team is not None
    assert team["team_number"] == "C1"


@pytest.mark.asyncio
async def test_get_team_by_number_not_found():
    team = await get_team_by_number("NONEXISTENT")
    assert team is None


@pytest.mark.asyncio
async def test_add_team_member():
    await create_user(2001, "Участник", "09.03.01", "seeker")
    team = await create_team("D1", 1001)
    added = await add_team_member(team["id"], 2001, "member")
    assert added is True
    members = await get_team_members(team["id"])
    assert len(members) == 1
    assert members[0]["telegram_id"] == 2001
    assert members[0]["member_role"] == "member"


@pytest.mark.asyncio
async def test_add_team_member_duplicate():
    await create_user(2002, "Участник2", "09.03.01", "seeker")
    team = await create_team("E1", 1001)
    await add_team_member(team["id"], 2002, "member")
    added = await add_team_member(team["id"], 2002, "member")
    assert added is False


@pytest.mark.asyncio
async def test_is_user_in_any_team():
    await create_user(2003, "Участник3", "09.03.01", "seeker")
    assert await is_user_in_any_team(2003) is False
    team = await create_team("F1", 1001)
    await add_team_member(team["id"], 2003, "member")
    assert await is_user_in_any_team(2003) is True


@pytest.mark.asyncio
async def test_add_member_then_delete_user():
    await create_user(2004, "Участник4", "09.03.01", "seeker")
    team = await create_team("G1", 1001)
    await add_team_member(team["id"], 2004, "member")
    deleted = await delete_user(2004)
    assert deleted is True
    user = await get_user(2004)
    assert user is None
    assert await is_user_in_any_team(2004) is True


@pytest.mark.asyncio
async def test_get_teams_by_creator():
    await create_team("H1", 3001)
    await create_team("H2", 3001)
    await create_team("H3", 3002)
    teams = await get_teams_by_creator(3001)
    assert len(teams) == 2


@pytest.mark.asyncio
async def test_remove_team_member():
    await create_user(2005, "Участник5", "09.03.01", "seeker")
    team = await create_team("I1", 1001)
    await add_team_member(team["id"], 2005, "member")
    removed = await remove_team_member(team["id"], 2005)
    assert removed is True
    members = await get_team_members(team["id"])
    assert len(members) == 0
    assert await is_user_in_any_team(2005) is False


@pytest.mark.asyncio
async def test_remove_team_member_not_found():
    team = await create_team("J1", 1001)
    removed = await remove_team_member(team["id"], 999999)
    assert removed is False


@pytest.mark.asyncio
async def test_get_user_team():
    await create_user(2006, "Участник6", "09.03.01", "seeker")
    team = await create_team("K1", 1001)
    await add_team_member(team["id"], 2006, "member")
    user_team = await get_user_team(2006)
    assert user_team is not None
    assert user_team["team_number"] == "K1"
    assert user_team["member_role"] == "member"


@pytest.mark.asyncio
async def test_get_user_team_not_in_team():
    user_team = await get_user_team(999999)
    assert user_team is None


@pytest.mark.asyncio
async def test_available_users_excludes_team_members():
    await create_user(2010, "Свободный", "09.03.01", "seeker")
    await create_user(2011, "В команде", "09.03.03", "seeker")
    team = await create_team("L1", 3010)
    await add_team_member(team["id"], 2011, "member")

    available = await get_available_users_by_role("seeker")

    assert [user["telegram_id"] for user in available] == [2010]


@pytest.mark.asyncio
async def test_get_team_member_returns_role_and_contact_id():
    await create_user(2012, "Контакт", "09.03.01", "seeker")
    team = await create_team("M1", 3011)
    await add_team_member(team["id"], 2012, "member")

    membership = await get_team_member(team["id"], 2012)

    assert membership["telegram_id"] == 2012
    assert membership["member_role"] == "member"
