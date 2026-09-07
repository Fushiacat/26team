from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.db import create_user, get_user
from src.handlers.profile import _get_team_info, _profile_text
from src.keyboards import (
    direction_keyboard, role_keyboard, desired_role_keyboard,
    profile_keyboard, DESIRED_ROLES,
)

router = Router()

BACK_TO_PROFILE = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
])


class RegistrationForm(StatesGroup):
    waiting_name = State()
    waiting_role = State()
    waiting_direction = State()
    waiting_desired_role = State()
    waiting_about = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user:
        team_info = await _get_team_info(message.from_user.id)
        await message.answer(
            f"С возвращением, {user['name']}!\n\n{_profile_text(user, team_info)}",
            reply_markup=profile_keyboard(
                user["role"],
                team_info["members"] if team_info else None,
            ),
        )
        return
    await message.answer(
        "Привет! Я помогу тебе найти команду на хакатоне.\n"
        "Давай заполним анкету. Как тебя зовут?"
    )
    await state.set_state(RegistrationForm.waiting_name)


@router.message(RegistrationForm.waiting_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуй снова.")
        return
    await state.update_data(name=name)
    await message.answer(
        f"Приятно познакомиться, {name}!\nВыбери роль:",
        reply_markup=role_keyboard()
    )
    await state.set_state(RegistrationForm.waiting_role)


@router.callback_query(RegistrationForm.waiting_role, F.data.startswith("role:"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    await state.update_data(role=role)
    if role == "seeker":
        await callback.message.edit_text(
            "Выбери своё направление:",
            reply_markup=direction_keyboard()
        )
        await state.set_state(RegistrationForm.waiting_direction)
    else:
        data = await state.get_data()
        await create_user(
            telegram_id=callback.from_user.id,
            name=data["name"],
            direction=None,
            role=role,
        )
        await state.clear()
        await callback.message.edit_text(
            f"Анкета сохранена!\n\n"
            f"Имя: {data['name']}\n"
            f"Роль: Наставник",
            reply_markup=profile_keyboard("organizer"),
        )
    await callback.answer()


@router.callback_query(RegistrationForm.waiting_direction, F.data.startswith("dir:"))
async def process_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split(":")[1]
    await state.update_data(direction=direction)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"drole:{code}")]
        for code, name in DESIRED_ROLES.items()
    ])
    kb.inline_keyboard.append(
        [InlineKeyboardButton(text="К анкете", callback_data="back:profile")]
    )
    await callback.message.edit_text(
        "Выбери желаемую роль в команде:",
        reply_markup=kb
    )
    await state.set_state(RegistrationForm.waiting_desired_role)
    await callback.answer()


@router.callback_query(RegistrationForm.waiting_desired_role, F.data.startswith("drole:"))
async def process_desired_role(callback: CallbackQuery, state: FSMContext):
    desired_role = callback.data.split(":")[1]
    await state.update_data(desired_role=desired_role)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="about:skip")],
        [InlineKeyboardButton(text="К анкете", callback_data="back:profile")],
    ])
    await callback.message.edit_text(
        "Расскажи о себе (максимум 200 символов):\n"
        "Свой опыт, навыки или то, что считаешь важным.",
        reply_markup=kb
    )
    await state.set_state(RegistrationForm.waiting_about)
    await callback.answer()


@router.callback_query(RegistrationForm.waiting_about, F.data == "about:skip")
async def process_about_skip(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await create_user(
        telegram_id=callback.from_user.id,
        name=data["name"],
        direction=data["direction"],
        role=data["role"],
        desired_role=data["desired_role"],
    )
    await state.clear()
    await callback.message.edit_text(
        f"Анкета сохранена!\n\n"
        f"Имя: {data['name']}\n"
        f"Направление: {data['direction']}\n"
        f"Желаемая роль: {DESIRED_ROLES[data['desired_role']]}\n"
        f"Роль: Участник",
        reply_markup=profile_keyboard("seeker"),
    )
    await callback.answer()


@router.message(RegistrationForm.waiting_about)
async def process_about(message: Message, state: FSMContext):
    about = message.text.strip()
    if len(about) > 200:
        await message.answer("Текст слишком длинный. Максимум 200 символов. Попробуй снова.")
        return
    await state.update_data(about_text=about)
    data = await state.get_data()
    await create_user(
        telegram_id=message.from_user.id,
        name=data["name"],
        direction=data["direction"],
        role=data["role"],
        desired_role=data["desired_role"],
        about_text=about,
    )
    await state.clear()
    await message.answer(
        f"Анкета сохранена!\n\n"
        f"Имя: {data['name']}\n"
        f"Направление: {data['direction']}\n"
        f"Желаемая роль: {DESIRED_ROLES[data['desired_role']]}\n"
        f"О себе: {about}\n"
        f"Роль: Участник",
        reply_markup=profile_keyboard("seeker"),
    )


@router.callback_query(F.data == "back:profile")
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("У тебя ещё нет анкеты. Нажми /start чтобы создать.")
        await callback.answer()
        return
    team_info = await _get_team_info(callback.from_user.id)
    await callback.message.edit_text(
        _profile_text(user, team_info),
        reply_markup=profile_keyboard(
            user["role"],
            team_info["members"] if team_info else None,
        ),
    )
    await callback.answer()
