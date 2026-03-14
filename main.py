# main.py
import asyncio
from loader import dp, bot, db

from handlers.start import router as start_router  
from handlers.admin import router as admin_router 
from handlers.callbacks import router as callbacks_router
from handlers.registration import router as registration_router
from handlers.common import router as common_router
from states import Registration, CodeState, BroadcastState

async def main():
    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(callbacks_router)
    dp.include_router(registration_router)
    dp.include_router(common_router)
    # Создаём таблицы (включая таблицу codes)
    await db.create_tables()
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")