from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.db import create_user, get_user
from src.keyboards import direction_keyboard, role_keyboard

router = Router()


class RegistrationForm(StatesGroup):
    waiting_name = State()
    waiting_direction = State()
    waiting_role = State()
    waiting_description = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user:
        role_text = "Ищу команду" if user["role"] == "seeker" else "Собираю команду"
        await message.answer(
            f"С возвращением, {user['name']}!\n"
            f"Твоя анкета:\n"
            f"Имя: {user['name']}\n"
            f"Направление: {user['direction']}\n"
            f"Роль: {role_text}\n"
            f"Описание: {user['description']}\n\n"
            f"Используй /me для просмотра, /edit для редактирования, /find для поиска."
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
        f"Приятно познакомиться, {name}!\n"
        "Выбери своё направление:",
        reply_markup=direction_keyboard()
    )
    await state.set_state(RegistrationForm.waiting_direction)


@router.callback_query(RegistrationForm.waiting_direction, F.data.startswith("dir:"))
async def process_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split(":")[1]
    await state.update_data(direction=direction)
    await callback.message.edit_text(
        f"Направление: {direction}\nТеперь выбери роль:",
        reply_markup=role_keyboard()
    )
    await state.set_state(RegistrationForm.waiting_role)
    await callback.answer()


@router.callback_query(RegistrationForm.waiting_role, F.data.startswith("role:"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    await state.update_data(role=role)
    role_text = "Ищу команду" if role == "seeker" else "Собираю команду"
    await callback.message.edit_text(
        f"Роль: {role_text}\n"
        "Опиши себя кратко: навыки, опыт, что ищешь на хакатоне.\n"
        "Максимум 500 символов."
    )
    await state.set_state(RegistrationForm.waiting_description)
    await callback.answer()


@router.message(RegistrationForm.waiting_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if len(description) > 500:
        await message.answer("Описание слишком длинное (макс. 500 символов). Сократи.")
        return
    data = await state.get_data()
    await create_user(
        telegram_id=message.from_user.id,
        name=data["name"],
        direction=data["direction"],
        role=data["role"],
        description=description,
    )
    await state.clear()
    role_text = "Ищу команду" if data["role"] == "seeker" else "Собираю команду"
    await message.answer(
        "Анкета сохранена!\n\n"
        f"Имя: {data['name']}\n"
        f"Направление: {data['direction']}\n"
        f"Роль: {role_text}\n"
        f"Описание: {description}\n\n"
        "Команды:\n"
        "/me — посмотреть анкету\n"
        "/edit — редактировать анкету\n"
        "/find — найти подходящих"
    )
