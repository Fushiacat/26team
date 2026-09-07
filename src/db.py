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
                direction TEXT CHECK(direction IN ('09.03.01', '09.03.03', '09.03.04', '27.03.04')),
                role TEXT NOT NULL CHECK(role IN ('seeker', 'organizer')),
                desired_role TEXT,
                about_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN desired_role TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN about_text TEXT")
        except Exception:
            pass
        await db.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_number TEXT UNIQUE NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                member_role TEXT NOT NULL CHECK(member_role IN ('mentor', 'member')),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id),
                UNIQUE(team_id, telegram_id)
            )
        """)
        await db.commit()


async def create_user(telegram_id: int, name: str, direction: str, role: str, desired_role: str | None = None, about_text: str | None = None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (telegram_id, name, direction, role, desired_role, about_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, name, direction, role, desired_role, about_text))
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


async def delete_user(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_users_by_role(role: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE role = ?", (role,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_available_users_by_role(role: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT u.* FROM users u "
            "WHERE u.role = ? AND NOT EXISTS ("
            "SELECT 1 FROM team_members tm WHERE tm.telegram_id = u.telegram_id"
            ")",
            (role,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def create_team(team_number: str, created_by: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO teams (team_number, created_by) VALUES (?, ?)",
                (team_number, created_by)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            return None
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM teams WHERE team_number = ?", (team_number,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_team_by_number(team_number: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM teams WHERE team_number = ?", (team_number,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_team_by_id(team_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM teams WHERE id = ?", (team_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_team_member(team_id: int, telegram_id: int, member_role: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO team_members (team_id, telegram_id, member_role) VALUES (?, ?, ?)",
                (team_id, telegram_id, member_role)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_team_members(team_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT tm.*, u.name, u.direction, u.desired_role, u.about_text
            FROM team_members tm
            JOIN users u ON tm.telegram_id = u.telegram_id
            WHERE tm.team_id = ?
        """, (team_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_team_member(team_id: int, telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM team_members WHERE team_id = ? AND telegram_id = ?",
            (team_id, telegram_id),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_teams_by_creator(telegram_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM teams WHERE created_by = ?", (telegram_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def is_user_in_any_team(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM team_members WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def remove_team_member(team_id: int, telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM team_members WHERE team_id = ? AND telegram_id = ?",
            (team_id, telegram_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_user_team(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT tm.*, t.team_number FROM team_members tm "
            "JOIN teams t ON tm.team_id = t.id WHERE tm.telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
