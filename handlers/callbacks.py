#обработку нажатий Inline-кнопок выносят в отдельный файл. Это те самые действия, 
# которые происходят «без текста», когда пользователь кликает по меню под сообщением.
# handlers/callbacks.py
from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from database.data import Database
from loader import bot, db
from config import ADMIN_ID
import pandas as pd
import io
from aiogram.types import BufferedInputFile
import aiosqlite
from utils.code_generator import CodeGenerator

router = Router()


# Проверка админа
def is_admin(callback: types.CallbackQuery):
    return callback.from_user.id == ADMIN_ID

@router.callback_query(F.data == "admin_generate_codes")
async def generate_access_codes(callback: types.CallbackQuery):
    if not is_admin(callback):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    # Используем глобальную базу данных из loader.py
    code_gen = CodeGenerator(db)

    try:
        # Генерируем 10 кодов и получаем их список
        generated_codes = await code_gen.generate_and_save_codes(10)
        # Формируем красивый список кодов
        codes_list = "\n".join(f"🔑 {code}" for code in generated_codes)
        response = f"✅ Сгенерировано 10 кодов доступа:\n\n{codes_list}\n\nПроверьте базу данных, чтобы убедиться, что коды сохранены."
        await callback.message.edit_text(response)
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при генерации кодов: {e}")

    await callback.answer()
    
# 🔹 Обработка: Все пользователи
@router.callback_query(F.data == "admin_users")
async def show_users(callback: types.CallbackQuery):
    if not is_admin(callback):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return
    
    async with aiosqlite.connect(db.db_name) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT user_id, name, birthday FROM users")
        rows = await cursor.fetchall()

    if not rows:
        await callback.message.edit_text("📭 Нет зарегистрированных пользователей.")
        return

    output = "👥 Список пользователей:\n\n"
    for i, row in enumerate(rows, 1):
        output += f"{i}. {row['name']} | 🎂 {row['birthday']} | ID: {row['user_id']}\n"

    await callback.message.edit_text(output)
    await callback.answer()  # Убираем "часики"


# 🔹 Обработка: Выгрузить Excel
@router.callback_query(F.data == "admin_export")
async def export_excel(callback: types.CallbackQuery):
    if not is_admin(callback):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return
    
    async with aiosqlite.connect(db.db_name) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        df = pd.DataFrame([dict(row) for row in rows])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Пользователи')

    buffer.seek(0)
    file = BufferedInputFile(buffer.getvalue(), filename="отчёт_пользователи.xlsx")

    await callback.message.answer_document(file)
    await callback.answer("✅ Отчёт отправлен")
    buffer.close()


# 🔹 Обработка: Рассылка
@router.callback_query(F.data == "admin_broadcast")
async def ask_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return
    
    await callback.message.edit_text("✉️ Введите сообщение для рассылки всем пользователям:")
    await state.set_state("awaiting_broadcast")
    await callback.answer()