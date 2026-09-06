from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.db import get_user, update_user
from src.keyboards import direction_keyboard, role_keyboard, edit_keyboard

router = Router()


class EditForm(StatesGroup):
    choosing_field = State()
    editing_name = State()
    editing_direction = State()
    editing_role = State()
    editing_description = State()


@router.message(F.text == "/me")
async def cmd_me(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("У тебя ещё нет анкеты. Нажми /start чтобы создать.")
        return
    role_text = "Ищу команду" if user["role"] == "seeker" else "Собираю команду"
    await message.answer(
        f"Твоя анкета:\n\n"
        f"Имя: {user['name']}\n"
        f"Направление: {user['direction']}\n"
        f"Роль: {role_text}\n"
        f"Описание: {user['description']}\n\n"
        f"Нажми /edit чтобы изменить.",
        reply_markup=edit_keyboard()
    )


@router.callback_query(F.data == "edit:start")
async def edit_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Что хочешь изменить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Имя", callback_data="edit:name")],
            [InlineKeyboardButton(text="Направление", callback_data="edit:direction")],
            [InlineKeyboardButton(text="Роль", callback_data="edit:role")],
            [InlineKeyboardButton(text="Описание", callback_data="edit:description")],
        ])
    )
    await state.set_state(EditForm.choosing_field)
    await callback.answer()


@router.callback_query(EditForm.choosing_field, F.data.startswith("edit:"))
async def edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":")[1]
    if field == "name":
        await callback.message.edit_text("Введи новое имя (2-50 символов):")
        await state.set_state(EditForm.editing_name)
    elif field == "direction":
        await callback.message.edit_text("Выбери новое направление:", reply_markup=direction_keyboard())
        await state.set_state(EditForm.editing_direction)
    elif field == "role":
        await callback.message.edit_text("Выбери новую роль:", reply_markup=role_keyboard())
        await state.set_state(EditForm.editing_role)
    elif field == "description":
        await callback.message.edit_text("Введи новое описание (до 500 символов):")
        await state.set_state(EditForm.editing_description)
    await callback.answer()


@router.message(EditForm.editing_name)
async def process_edit_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов.")
        return
    await update_user(message.from_user.id, name=name)
    await state.clear()
    await message.answer("Имя обновлено!")


@router.callback_query(EditForm.editing_direction, F.data.startswith("dir:"))
async def process_edit_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split(":")[1]
    await update_user(callback.from_user.id, direction=direction)
    await state.clear()
    await callback.message.edit_text("Направление обновлено!")
    await callback.answer()


@router.callback_query(EditForm.editing_role, F.data.startswith("role:"))
async def process_edit_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    await update_user(callback.from_user.id, role=role)
    await state.clear()
    await callback.message.edit_text("Роль обновлена!")
    await callback.answer()


@router.message(EditForm.editing_description)
async def process_edit_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if len(description) > 500:
        await message.answer("Описание слишком длинное (макс. 500 символов).")
        return
    await update_user(message.from_user.id, description=description)
    await state.clear()
    await message.answer("Описание обновлено!")
