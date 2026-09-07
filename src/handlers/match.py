from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from src.db import get_user, delete_user, get_available_users_by_role, get_user_team

router = Router()


def _candidate_text(candidate: dict) -> str:
    direction = f"\nНаправление: {candidate['direction']}" if candidate.get("direction") else ""
    desired_role = f"\nИщет роль: {candidate['desired_role']}" if candidate.get("desired_role") else ""
    about = f"\nО себе: {candidate['about_text']}" if candidate.get("about_text") else ""
    return f"{candidate['name']}{direction}{desired_role}{about}"


@router.message(F.text == "/find")
async def cmd_find(message: Message):
    if message.from_user is None:
        return
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("У тебя ещё нет анкеты. Нажми /start чтобы создать.")
        return
    if await get_user_team(message.from_user.id):
        await message.answer("Ты уже состоишь в команде. Посмотри её состав в /me.")
        return

    target_role = "organizer" if user["role"] == "seeker" else "seeker"
    candidates = [
        candidate for candidate in await get_available_users_by_role(target_role)
        if candidate["telegram_id"] != message.from_user.id
    ]
    if not candidates:
        await message.answer("Пока нет подходящих анкет.")
        return
    for candidate in candidates:
        await message.answer(
            _candidate_text(candidate),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="✉️ Связаться",
                    url=f"tg://user?id={candidate['telegram_id']}",
                )
            ]]),
        )


@router.callback_query(F.data.startswith("deluser:"))
async def delete_user_callback(callback: CallbackQuery):
    if (
        callback.from_user is None
        or callback.data is None
        or not isinstance(callback.message, Message)
    ):
        await callback.answer()
        return
    caller = await get_user(callback.from_user.id)
    if not caller or caller["role"] != "organizer":
        await callback.answer("Только наставники могут удалять анкеты.", show_alert=True)
        return
    target_id = int(callback.data.split(":")[1])
    deleted = await delete_user(target_id)
    if deleted:
        await callback.message.edit_text("Анкета удалена.")
    else:
        await callback.message.edit_text("Анкета уже удалена.")
    await callback.answer()
