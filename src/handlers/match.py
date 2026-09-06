from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from src.db import get_user, get_users_by_role

router = Router()


@router.message(F.text == "/find")
async def cmd_find(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала заполни анкету: /start")
        return

    target_role = "organizer" if user["role"] == "seeker" else "seeker"
    candidates = await get_users_by_role(target_role)

    if not candidates:
        await message.answer("Пока нет подходящих анкет. Попробуй позже!")
        return

    if len(candidates) > 10:
        await message.answer(f"Найдено {len(candidates)} анкет. Показываю все:")

    for candidate in candidates:
        role_text = "Ищу команду" if candidate["role"] == "seeker" else "Собираю команду"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Связаться",
                url=f"tg://user?id={candidate['telegram_id']}"
            )]
        ])
        await message.answer(
            f"Имя: {candidate['name']}\n"
            f"Направление: {candidate['direction']}\n"
            f"Роль: {role_text}\n"
            f"Описание: {candidate['description']}",
            reply_markup=keyboard,
        )
