import aiosqlite
import sqlite3
from config import DB_NAME
from database.data import Database

# Асинхронная версия функций для работы с базой данных
async def init_db():
    """Таблица codes уже создается в db.create_tables()."""
    pass

async def add_code(code: str):
    """Добавляет новый код в базу данных."""
    db = Database()
    async with aiosqlite.connect(db.db_name) as conn:
        await conn.execute('INSERT OR REPLACE INTO codes (code) VALUES (?)', (code,))
        await conn.commit()

async def check_activation_code(code: str) -> bool:
    """Проверяет, существует ли код и не использован ли он."""
    db = Database()
    async with aiosqlite.connect(db.db_name) as conn:
        # Добавим логирование
        print(f"[DEBUG] Проверка кода в базе: '{code}'")
        # Выведем все коды из таблицы для отладки
        async with conn.execute('SELECT code, is_used FROM codes') as debug_cursor:
            all_codes = await debug_cursor.fetchall()
            print(f"[DEBUG] Все коды в таблице codes: {dict(all_codes)}")
            
        async with conn.execute('SELECT is_used, code FROM codes WHERE code = ?', (code,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                print(f"[DEBUG] Код '{code}' не найден в таблице codes.")
                return False  # Кода нет в базе
            is_used, stored_code = row
            print(f"[DEBUG] Найден код: '{stored_code}', is_used={is_used}")
            return not is_used  # True, если код не использован

async def use_code(code: str, user_id: int):
    """Помечает код как использованный и связывает с пользователем."""
    db = Database()
    async with aiosqlite.connect(db.db_name) as conn:
        await conn.execute('''
            UPDATE codes 
            SET is_used = TRUE, used_by = ? 
            WHERE code = ?
        ''', (user_id, code))
        await conn.commit()
        return conn.total_changes > 0