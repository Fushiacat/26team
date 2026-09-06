from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

DIRECTIONS = {
    "09.03.01": "Информатика",
    "09.03.03": "Прикладная математика",
    "09.03.04": "Информационная безопасность",
    "27.03.04": "Программная инженерия",
}


def direction_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{code} — {name}", callback_data=f"dir:{code}")]
        for code, name in DIRECTIONS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ищу команду", callback_data="role:seeker")],
        [InlineKeyboardButton(text="Собираю команду", callback_data="role:organizer")],
    ])


def edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data="edit:start")],
    ])
