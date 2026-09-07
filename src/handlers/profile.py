from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.db import get_user, update_user, delete_user, get_user_team, get_team_by_id, get_team_members
from src.keyboards import (
    direction_keyboard, role_keyboard, profile_keyboard,
    desired_role_keyboard, DESIRED_ROLES,
)

router = Router()

BACK_TO_PROFILE = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
])


async def _get_team_info(telegram_id: int) -> dict | None:
    team = await get_user_team(telegram_id)
    if not team:
        return None
    members = await get_team_members(team["team_id"])
    return {
        "team_number": team["team_number"],
        "members_count": len(members),
        "members": [
            {
                "name": m["name"],
                "direction": m["direction"],
                "telegram_id": m["telegram_id"],
                "member_role": m["member_role"],
            }
            for m in members
        ],
    }


class EditForm(StatesGroup):
    choosing_field = State()
    editing_name = State()
    editing_direction = State()
    editing_role = State()
    editing_desired_role = State()
    editing_about = State()


def _profile_text(user: dict, team_info: dict | None = None) -> str:
    role_text = "Участник" if user["role"] == "seeker" else "Наставник"
    direction_line = f"Направление: {user['direction']}\n" if user["role"] == "seeker" else ""
    desired_role_line = f"Желаемая роль: {DESIRED_ROLES.get(user['desired_role'], user['desired_role'])}\n" if user.get("desired_role") else ""
    about_line = f"О себе: {user['about_text']}\n" if user.get("about_text") else ""
    team_line = ""
    if team_info:
        team_line = f"\nКоманда: «{team_info['team_number']}»  ({team_info['members_count']} чел.)\n"
        if team_info.get("members"):
            team_line += "Состав:\n"
            for m in team_info["members"]:
                member_role = "наставник" if m["member_role"] == "mentor" else "участник"
                team_line += (
                    f"  • {m['name']} ({member_role})\n"
                    f"    Контакт: tg://user?id={m['telegram_id']}\n"
                )
    return (
        f"Твоя анкета:\n\n"
        f"Имя: {user['name']}\n"
        f"{direction_line}"
        f"{desired_role_line}"
        f"{about_line}"
        f"Роль: {role_text}"
        f"{team_line}"
    )


@router.message(F.text == "/me")
async def cmd_me(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("У тебя ещё нет анкеты. Нажми /start чтобы создать.")
        return
    team_info = await _get_team_info(message.from_user.id)
    await message.answer(
        _profile_text(user, team_info),
        reply_markup=profile_keyboard(user["role"], team_info["members"] if team_info else None),
    )


@router.message(F.text == "/edit")
async def cmd_edit(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("У тебя ещё нет анкеты. Нажми /start чтобы создать.")
        return
    buttons = [
        [InlineKeyboardButton(text="Имя", callback_data="edit:name")],
        [InlineKeyboardButton(text="Роль", callback_data="edit:role")],
    ]
    if user["role"] == "seeker":
        buttons.insert(1, [InlineKeyboardButton(text="Направление", callback_data="edit:direction")])
        buttons.insert(2, [InlineKeyboardButton(text="Желаемая роль", callback_data="edit:desired_role")])
        buttons.insert(3, [InlineKeyboardButton(text="О себе", callback_data="edit:about")])
    buttons.append([InlineKeyboardButton(text="К анкете", callback_data="back:profile")])
    await message.answer(
        "Что хочешь изменить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(EditForm.choosing_field)


@router.callback_query(F.data == "edit:start")
async def edit_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="Имя", callback_data="edit:name")],
        [InlineKeyboardButton(text="Роль", callback_data="edit:role")],
    ]
    if user and user["role"] == "seeker":
        buttons.insert(1, [InlineKeyboardButton(text="Направление", callback_data="edit:direction")])
        buttons.insert(2, [InlineKeyboardButton(text="Желаемая роль", callback_data="edit:desired_role")])
        buttons.insert(3, [InlineKeyboardButton(text="О себе", callback_data="edit:about")])
    buttons.append([InlineKeyboardButton(text="К анкете", callback_data="back:profile")])
    await callback.message.edit_text(
        "Что хочешь изменить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(EditForm.choosing_field)
    await callback.answer()


@router.callback_query(EditForm.choosing_field, F.data.startswith("edit:"))
async def edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":")[1]
    if field == "name":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
        ])
        await callback.message.edit_text("Введи новое имя (2-50 символов):", reply_markup=kb)
        await state.set_state(EditForm.editing_name)
    elif field == "direction":
        kb = direction_keyboard()
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text="К анкете", callback_data="back:profile")]
        )
        await callback.message.edit_text("Выбери новое направление:", reply_markup=kb)
        await state.set_state(EditForm.editing_direction)
    elif field == "role":
        kb = role_keyboard()
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text="К анкете", callback_data="back:profile")]
        )
        await callback.message.edit_text("Выбери новую роль:", reply_markup=kb)
        await state.set_state(EditForm.editing_role)
    elif field == "desired_role":
        kb = desired_role_keyboard()
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text="К анкете", callback_data="back:profile")]
        )
        await callback.message.edit_text("Выбери новую желаемую роль:", reply_markup=kb)
        await state.set_state(EditForm.editing_desired_role)
    elif field == "about":
        skip_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="about:skip")],
            [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
        ])
        await callback.message.edit_text(
            "Расскажи о себе (максимум 200 символов):",
            reply_markup=skip_kb
        )
        await state.set_state(EditForm.editing_about)
    await callback.answer()


async def _saved_profile_text(telegram_id: int) -> str:
    user = await get_user(telegram_id)
    if not user:
        return ""
    team_info = await _get_team_info(telegram_id)
    return _profile_text(user, team_info)


async def _saved_profile_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    user = await get_user(telegram_id)
    team_info = await _get_team_info(telegram_id)
    return profile_keyboard(
        user["role"],
        team_info["members"] if team_info else None,
    )


@router.message(EditForm.editing_name)
async def process_edit_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов.")
        return
    await update_user(message.from_user.id, name=name)
    await state.clear()
    user = await get_user(message.from_user.id)
    team_info = await _get_team_info(message.from_user.id)
    await message.answer(
        _profile_text(user, team_info),
        reply_markup=profile_keyboard(user["role"], team_info["members"] if team_info else None),
    )


@router.callback_query(EditForm.editing_direction, F.data.startswith("dir:"))
async def process_edit_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split(":")[1]
    await state.update_data(editing_direction=direction)
    kb = desired_role_keyboard()
    kb.inline_keyboard.append(
        [InlineKeyboardButton(text="К анкете", callback_data="back:profile")]
    )
    await callback.message.edit_text(
        "Выбери новую желаемую роль:",
        reply_markup=kb
    )
    await state.set_state(EditForm.editing_desired_role)
    await callback.answer()


@router.callback_query(EditForm.editing_role, F.data.startswith("role:"))
async def process_edit_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    if role == "organizer":
        await update_user(callback.from_user.id, role=role, direction=None, desired_role=None, about_text=None)
        await state.clear()
        user = await get_user(callback.from_user.id)
        team_info = await _get_team_info(callback.from_user.id)
        await callback.message.edit_text(
            _profile_text(user, team_info),
            reply_markup=profile_keyboard(user["role"], team_info["members"] if team_info else None),
        )
    else:
        await update_user(callback.from_user.id, role=role)
        await state.clear()
        kb = direction_keyboard()
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text="К анкете", callback_data="back:profile")]
        )
        await callback.message.edit_text("Выбери направление:", reply_markup=kb)
        await state.set_state(EditForm.editing_direction)
    await callback.answer()


@router.callback_query(EditForm.editing_desired_role, F.data.startswith("drole:"))
async def process_edit_desired_role(callback: CallbackQuery, state: FSMContext):
    desired_role = callback.data.split(":")[1]
    data = await state.get_data()
    update_fields = {"desired_role": desired_role}
    if "editing_direction" in data:
        update_fields["direction"] = data["editing_direction"]
    await update_user(callback.from_user.id, **update_fields)
    await state.clear()
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        _profile_text(user, await _get_team_info(callback.from_user.id)),
        reply_markup=await _saved_profile_keyboard(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(EditForm.editing_about, F.data == "about:skip")
async def process_edit_about_skip(callback: CallbackQuery, state: FSMContext):
    await update_user(callback.from_user.id, about_text=None)
    await state.clear()
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        _profile_text(user, await _get_team_info(callback.from_user.id)),
        reply_markup=await _saved_profile_keyboard(callback.from_user.id),
    )
    await callback.answer()


@router.message(EditForm.editing_about)
async def process_edit_about(message: Message, state: FSMContext):
    about = message.text.strip()
    if len(about) > 200:
        await message.answer("Текст слишком длинный. Максимум 200 символов. Попробуй снова.")
        return
    await update_user(message.from_user.id, about_text=about)
    await state.clear()
    user = await get_user(message.from_user.id)
    team_info = await _get_team_info(message.from_user.id)
    await message.answer(
        _profile_text(user, team_info),
        reply_markup=await _saved_profile_keyboard(message.from_user.id),
    )


@router.message(F.text == "/delete")
async def cmd_delete(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("У тебя ещё нет анкеты.")
        return
    await message.answer(
        "Ты точно хочешь удалить свою анкету?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да, удалить", callback_data="delete:confirm")],
            [InlineKeyboardButton(text="Нет, оставить", callback_data="back:profile")],
        ])
    )


@router.callback_query(F.data == "delete:confirm")
async def delete_confirm(callback: CallbackQuery):
    await delete_user(callback.from_user.id)
    await callback.message.edit_text("Анкета удалена.")
    await callback.answer()


@router.callback_query(F.data == "delete:cancel")
async def delete_cancel(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if user:
        team_info = await _get_team_info(callback.from_user.id)
        await callback.message.edit_text(
            _profile_text(user, team_info),
            reply_markup=await _saved_profile_keyboard(callback.from_user.id),
        )
    else:
        await callback.message.edit_text("Анкета осталась на месте.")
    await callback.answer()
