import secrets
import string
from database.data import Database
import aiosqlite


def generate_code(length=6):
    """Генерирует случайный код из букв и цифр."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class CodeGenerator:
    def __init__(self, db: Database):
        self.db = db

    async def generate_and_save_codes(self, count: int):
        """Генерирует указанное количество кодов и сохраняет их в базу данных."""
        # Предположим, что у нас есть таблица access_codes с полями: code (TEXT), is_used (BOOLEAN)
        async with aiosqlite.connect(self.db.db_name) as conn:
            # Создаем таблицу, если она еще не существует
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS codes (
                    code TEXT PRIMARY KEY,
                    is_used BOOLEAN DEFAULT FALSE,
                    used_by INTEGER
                )
            ''')

            # Генерируем уникальные коды
            codes = set()
            while len(codes) < count:
                code = generate_code()
                codes.add(code)

            # Сохраняем коды в базу
            await conn.executemany(
                'INSERT OR IGNORE INTO codes (code) VALUES (?)',
                [(code,) for code in codes]
            )
            await conn.commit()

        # Добавим вывод сгенерированных кодов для отладки
        print(f"Сгенерировано и сохранено {len(codes)} кодов доступа.")
        print(f"Сгенерированные коды: {list(codes)}")
        return list(codes)