import aiosqlite
from config import DB_NAME


class Database:
    def __init__(self):
        self.db_name = DB_NAME

    async def create_tables(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    birthday TEXT NOT NULL
                )
            ''')
            # Создаем таблицу codes с нужной структурой
            await db.execute('''
                CREATE TABLE IF NOT EXISTS codes (
                    code TEXT PRIMARY KEY,
                    is_used BOOLEAN DEFAULT FALSE,
                    used_by INTEGER
                )
            ''')
            await db.commit()

    async def add_user(self, user_id: int, name: str, birthday: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users (user_id, name, birthday)
                VALUES (?, ?, ?)
            ''', (user_id, name, birthday))
            await db.commit()

    async def user_exists(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result is not None


    async def get_all_users(self):
        """Возвращает список всех пользователей."""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT user_id as telegram_id, name, birthday FROM users') as cursor:
                rows = await cursor.fetchall()
                # Преобразуем в список словарей
                return [{"telegram_id": r[0], "name": r[1], "birthday": r[2]} for r in rows]


    async def get_user(self, user_id: int):
        """Возвращает данные пользователя по его user_id."""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT name, birthday FROM users WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"name": row[0], "birthday": row[1]}
                return None