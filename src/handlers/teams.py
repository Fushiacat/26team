import aiosqlite
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.db import (
    DB_PATH, get_user, get_user_team, delete_user, get_available_users_by_role,
    create_team, get_team_by_number, get_team_by_id,
    add_team_member, remove_team_member, get_team_members, get_team_member,
    is_user_in_any_team,
)

router = Router()


class CreateTeamForm(StatesGroup):
    waiting_number = State()


class JoinTeamForm(StatesGroup):
    waiting_number = State()


def _team_management_text(team: dict, members: list[dict]) -> str:
    lines = [f"Команда «{team['team_number']}»  (участников: {len(members)})\n"]
    mentors = [m for m in members if m["member_role"] == "mentor"]
    players = [m for m in members if m["member_role"] == "member"]

    if mentors:
        lines.append("Наставники:")
        for m in mentors:
            lines.append(f"  • {m['name']}")
    if players:
        lines.append("Участники:")
        for m in players:
            dr = f", {m.get('desired_role', '')}" if m.get("desired_role") else ""
            lines.append(f"  • {m['name']} ({m['direction']}{dr})")
    if not mentors and not players:
        lines.append("Пока пусто.")

    return "\n".join(lines)


def _team_management_keyboard(
    team_id: int,
    members: list[dict],
    can_manage: bool = True,
) -> InlineKeyboardMarkup:
    buttons = []
    if can_manage:
        buttons.append([InlineKeyboardButton(text="➕ Добавить участника", callback_data=f"tm:add:{team_id}")])

    contact_buttons = []
    for m in members:
        contact_buttons.append(InlineKeyboardButton(
            text=f"✉️ {m['name']}",
            url=f"tg://user?id={m['telegram_id']}"
        ))
    if contact_buttons:
        rows = [contact_buttons[i:i+2] for i in range(0, len(contact_buttons), 2)]
        buttons.extend(rows)

    if can_manage:
        remove_buttons = []
        for m in members:
            if m["member_role"] == "member":
                remove_buttons.append(InlineKeyboardButton(
                    text=f"❌ {m['name']}",
                    callback_data=f"tm:remove:{team_id}:{m['telegram_id']}"
                ))
        if remove_buttons:
            rows = [remove_buttons[i:i+2] for i in range(0, len(remove_buttons), 2)]
            buttons.extend(rows)

    buttons.append([InlineKeyboardButton(text="К анкете", callback_data="back:profile")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def show_team_management(message: Message, team_id: int, viewer_id: int | None = None):
    team = await get_team_by_id(team_id)
    members = await get_team_members(team_id)
    text = _team_management_text(team, members)
    viewer_id = viewer_id if viewer_id is not None else message.from_user.id
    caller_membership = await get_team_member(team_id, viewer_id)
    kb = _team_management_keyboard(
        team_id,
        members,
        can_manage=bool(caller_membership and caller_membership["member_role"] == "mentor"),
    )
    await message.answer(text, reply_markup=kb)


@router.message(F.text == "/teams")
async def cmd_teams(message: Message):
    user = await get_user(message.from_user.id)
    if not user or user["role"] != "organizer":
        await message.answer("Эта команда доступна только наставникам.")
        return

    team = await get_user_team(message.from_user.id)
    if team:
        await show_team_management(message, team["team_id"])
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать команду", callback_data="team:create")],
        [InlineKeyboardButton(text="Вступить в команду", callback_data="team:join")],
        [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
    ])
    await message.answer("Управление командами:", reply_markup=keyboard)


@router.callback_query(F.data == "teams:start")
async def teams_start_callback(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user or user["role"] != "organizer":
        await callback.answer("Только наставники могут управлять командами.", show_alert=True)
        return

    team = await get_user_team(callback.from_user.id)
    if team:
        await callback.message.delete()
        await show_team_management(callback.message, team["team_id"], callback.from_user.id)
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать команду", callback_data="team:create")],
        [InlineKeyboardButton(text="Вступить в команду", callback_data="team:join")],
        [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
    ])
    await callback.message.edit_text("Управление командами:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "team:create")
async def team_create_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
    ])
    await callback.message.edit_text("Введи номер команды (например: 2, 18):", reply_markup=kb)
    await state.set_state(CreateTeamForm.waiting_number)
    await callback.answer()


@router.message(CreateTeamForm.waiting_number)
async def team_create_process(message: Message, state: FSMContext):
    team_number = message.text.strip()
    if len(team_number) < 1 or len(team_number) > 20:
        await message.answer("Номер должен быть от 1 до 20 символов. Попробуй снова.")
        return
    existing = await get_team_by_number(team_number)
    if existing:
        await message.answer(f"Команда с номером «{team_number}» уже существует. Выбери другой номер.")
        return
    team = await create_team(team_number, message.from_user.id)
    if not team:
        await message.answer("Ошибка при создании команды. Попробуй снова.")
        return
    await state.clear()
    await add_team_member(team["id"], message.from_user.id, "mentor")
    await show_team_management(message, team["id"])


@router.callback_query(F.data.startswith("tm:add:"))
async def tm_add_callback(callback: CallbackQuery):
    team_id = int(callback.data.split(":")[2])
    caller = await get_user(callback.from_user.id)
    caller_membership = await get_team_member(team_id, callback.from_user.id)
    if (
        not caller
        or caller["role"] != "organizer"
        or not caller_membership
        or caller_membership["member_role"] != "mentor"
    ):
        await callback.answer("Только наставники могут добавлять участников.", show_alert=True)
        return
    await callback.message.delete()
    seekers = await get_available_users_by_role("seeker")
    buttons = []
    for s in seekers:
        buttons.append([InlineKeyboardButton(
            text=f"➕ {s['name']} ({s['direction']})",
            callback_data=f"tm:doadd:{team_id}:{s['telegram_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"tm:back:{team_id}")])
    if len(buttons) == 1:
        buttons.insert(0, [InlineKeyboardButton(text="Нет доступных участников", callback_data="noop")])
    await callback.message.answer(
        "Выбери участника для добавления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("tm:doadd:"))
async def tm_doadd_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    team_id = int(parts[2])
    target_id = int(parts[3])

    caller_membership = await get_team_member(team_id, callback.from_user.id)
    if not caller_membership or caller_membership["member_role"] != "mentor":
        await callback.answer("Только наставник этой команды может добавлять участников.", show_alert=True)
        return

    user = await get_user(target_id)
    if not user:
        await callback.answer("Анкета уже удалена.", show_alert=True)
        return
    already = await is_user_in_any_team(target_id)
    if already:
        await callback.answer("Участник уже в команде.", show_alert=True)
        return

    team = await get_team_by_id(team_id)
    added = await add_team_member(team_id, target_id, "member")
    if added:
        members = await get_team_members(team_id)
        contacts = "\n".join(
            f"• {member['name']}: tg://user?id={member['telegram_id']}"
            for member in members
        )
        try:
            await callback.bot.send_message(
                target_id,
                f"Тебя добавили в команду «{team['team_number']}»!\n\n"
                f"Состав команды ({len(members)} чел.):\n{contacts}\n\n"
                "Выбери контакт, чтобы написать.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"✉️ {member['name']}", url=f"tg://user?id={member['telegram_id']}")]
                    for member in members
                ] + [
                    [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
                ])
            )
        except Exception:
            pass
        await callback.answer(f"{user['name']} добавлен!", show_alert=True)
        await callback.message.delete()
        await show_team_management(callback.message, team_id, callback.from_user.id)
    else:
        await callback.answer("Ошибка при добавлении.", show_alert=True)


@router.callback_query(F.data.startswith("tm:contact:"))
async def tm_contact_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    team_id = int(parts[2])
    target_id = int(parts[3])
    user = await get_user(callback.from_user.id)
    if not user or user["role"] != "organizer":
        await callback.answer("Только наставники могут писать участникам.", show_alert=True)
        return
    await callback.answer(f"Напиши участнику: tg://user?id={target_id}", show_alert=True)


@router.callback_query(F.data.startswith("tm:remove:"))
async def tm_remove_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    team_id = int(parts[2])
    target_id = int(parts[3])

    caller = await get_user(callback.from_user.id)
    if not caller or caller["role"] != "organizer":
        await callback.answer("Только наставники могут удалять участников.", show_alert=True)
        return

    removed = await remove_team_member(team_id, target_id)
    if removed:
        try:
            await callback.bot.send_message(
                target_id,
                "Тебя удалили из команды.",
            )
        except Exception:
            pass
        await callback.answer("Участник удалён из команды.", show_alert=True)
    else:
        await callback.answer("Участник не найден в команде.", show_alert=True)
    await callback.message.delete()
    await show_team_management(callback.message, team_id, callback.from_user.id)


@router.callback_query(F.data.startswith("tm:back:"))
async def tm_back_callback(callback: CallbackQuery):
    team_id = int(callback.data.split(":")[2])
    await callback.message.delete()
    await show_team_management(callback.message, team_id, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "team:join")
async def team_join_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
    ])
    await callback.message.edit_text(
        "Введи номер команды, в которую хочешь вступить:",
        reply_markup=kb
    )
    await state.set_state(JoinTeamForm.waiting_number)
    await callback.answer()


@router.message(JoinTeamForm.waiting_number)
async def team_join_process(message: Message, state: FSMContext):
    team_number = message.text.strip()
    team = await get_team_by_number(team_number)
    if not team:
        await message.answer(f"Команда «{team_number}» не найдена.")
        return
    already = await is_user_in_any_team(message.from_user.id)
    if already:
        await message.answer("Ты уже состоишь в команде.")
        return
    added = await add_team_member(team["id"], message.from_user.id, "mentor")
    if added:
        await state.clear()
        await show_team_management(message, team["id"])
    else:
        await message.answer("Ошибка при вступлении. Попробуй снова.")


@router.message(F.text == "/myteam")
async def cmd_myteam(message: Message):
    team = await get_user_team(message.from_user.id)
    if not team:
        await message.answer("Ты не состоишь ни в одной команде.")
        return
    members = await get_team_members(team["team_id"])
    team_data = await get_team_by_id(team["team_id"])
    text = _team_management_text(team_data, members)
    membership = await get_team_member(team["team_id"], message.from_user.id)
    kb = _team_management_keyboard(
        team["team_id"],
        members,
        can_manage=bool(membership and membership["member_role"] == "mentor"),
    )
    await message.answer(text, reply_markup=kb)
