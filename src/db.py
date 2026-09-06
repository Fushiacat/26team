import aiosqlite
import os

DB_PATH = "data/teammatch.db"


async def init_db():
    os.makedirs("data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('09.03.01', '09.03.03', '09.03.04', '27.03.04')),
                role TEXT NOT NULL CHECK(role IN ('seeker', 'organizer')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def create_user(telegram_id: int, name: str, direction: str, role: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (telegram_id, name, direction, role)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, name, direction, role))
        await db.commit()
        return await get_user(telegram_id)


async def get_user(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_user(telegram_id: int, **fields) -> dict | None:
    if not fields:
        return await get_user(telegram_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [telegram_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {set_clause} WHERE telegram_id = ?", values)
        await db.commit()
        return await get_user(telegram_id)


async def get_all_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_users_by_role(role: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE role = ?", (role,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
