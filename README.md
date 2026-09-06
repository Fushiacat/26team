# TeamMatch

Telegram-бот для быстрого матчинга участников хакатона.

## Запуск

1. Получи токен у [@BotFather](https://t.me/BotFather)
2. Создай файл `.env` (см. `.env.example`)
3. Установи зависимости: `pip install -e ".[dev]"`
4. Запусти: `python main.py`

## Тесты

```bash
pytest
```

## Структура

```
src/
├── bot.py          # инициализация бота
├── config.py       # загрузка .env
├── db.py           # SQLite + CRUD
├── handlers/
│   ├── start.py    # /start, регистрация
│   ├── profile.py  # /me, /edit
│   └── match.py    # /find, "Связаться"
└── keyboards.py    # inline-клавиатуры
```
