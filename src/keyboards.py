from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

DIRECTIONS = {
    "09.03.01": "Инфраструктура и технологии обработки информации",
    "09.03.03": "Аналитика и проектирование програмного обеспечения",
    "09.03.04": "Аритектура и разработка програмных систем",
    "27.03.04": "Разработка и эксплуатация систем управления",
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


DESIRED_ROLES = {
    "ba": "Бизнес-аналитик",
    "sa": "Системный аналитик",
    "dev": "Разработчик",
    "devops": "DevOps",
}


def desired_role_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"drole:{code}")]
        for code, name in DESIRED_ROLES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data="edit:start")],
    ])


def profile_keyboard(role: str = "seeker", team_members: list[dict] | None = None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Редактировать", callback_data="edit:start")],
        [InlineKeyboardButton(text="Удалить анкету", callback_data="delete:confirm")],
    ]
    if role == "organizer":
        buttons.insert(1, [InlineKeyboardButton(text="Управление командами", callback_data="teams:start")])
    if team_members:
        buttons.append([InlineKeyboardButton(text="Контакты команды", callback_data="noop")])
        for member in team_members:
            buttons.append([InlineKeyboardButton(
                text=f"✉️ {member['name']}",
                url=f"tg://user?id={member['telegram_id']}",
            )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
