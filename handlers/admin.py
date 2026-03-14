from aiogram import Router, types
from aiogram.filters import Command
from aiogram import F
from config import ADMIN_ID
from keyboards.admin import get_admin_keyboard
from keyboards.reply import get_main_keyboard
from utils.code_generator import CodeGenerator
from loader import db, bot

import re,aiosqlite
import pandas as pd
from io import BytesIO

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


class BroadcastState(StatesGroup):
    waiting_for_recipients = State()
    waiting_for_message = State()

class DeleteUserState(StatesGroup):
    waiting_for_user_id = State()



router = Router()

@router.message(F.text == "🗑️ Удалить пользователя")
async def handle_delete_user_start(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    await message.answer("Введите ID пользователя, которого нужно удалить:")
    await state.set_state(DeleteUserState.waiting_for_user_id)


@router.message(DeleteUserState.waiting_for_user_id)
async def handle_delete_user_id(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")
        return
    
    # Проверяем, существует ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден в базе данных.")
        await state.clear()
        return
    
    # Удаляем пользователя из базы данных
    async with aiosqlite.connect(db.db_name) as conn:
        await conn.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        await conn.commit()
    
    await message.answer(f"✅ Пользователь с ID {user_id} (Имя: {user['name']}) успешно удалён.")
    await state.clear()

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_ID


@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    # Отправляем приветствие и устанавливаем админскую клавиатуру
    await message.answer("🔐 Добро пожаловать, администратор! Используйте меню ниже.", reply_markup=get_admin_keyboard())
    
@router.message(F.text == "🔑 Сгенерировать коды доступа")
async def handle_generate_codes_text(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    # Копируем логику из callback-обработчика
    code_gen = CodeGenerator(db)
    try:
        codes = await code_gen.generate_and_save_codes(10)
        codes_list = "\n".join(f"🔑 {code}" for code in codes)
        await message.answer(f"✅ Сгенерировано 10 кодов доступа:\n\n{codes_list}")
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации кодов: {e}")


@router.message(F.text == "🔑 Коды доступа")
async def handle_available_codes(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    # Получаем список свободных кодов из базы данных
    async with aiosqlite.connect(db.db_name) as conn:
        async with conn.execute('SELECT code FROM codes WHERE is_used = FALSE') as cursor:
            rows = await cursor.fetchall()
            codes = [row[0] for row in rows]
    
    if codes:
        codes_list = "\n".join(f"🔑 {code}" for code in codes)
        await message.answer(f"✅ Свободные коды доступа:\n\n{codes_list}")
    else:
        await message.answer("❌ Нет свободных кодов доступа.")


@router.message(F.text == "📋 Все пользователи")
async def handle_all_users(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    users = await db.get_all_users()
    if users:
        users_list = "\n".join([f"👤 {user['name']} (ID: {user['telegram_id']})" for user in users])
        await message.answer(f"👥 Все зарегистрированные пользователи:\n\n{users_list}")
    else:
        await message.answer("📭 Нет зарегистрированных пользователей.")


@router.message(F.text == "📊 Выгрузить Excel")


async def handle_export_excel(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    # Получаем всех пользователей из базы данных
    users = await db.get_all_users()
    
    # Преобразуем данные в DataFrame
    df = pd.DataFrame(users)
    
    # Создаём BytesIO объект для хранения Excel-файла в памяти
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Пользователи')
    
    # Подготавливаем файл для отправки
    output.seek(0)  # Возвращаем указатель в начало
    file = types.BufferedInputFile(
        output.getvalue(), 
        filename="users_export.xlsx"
    )
    
    # Отправляем файл
    await message.answer_document(document=file, caption="📎 Экспорт базы данных в Excel")


@router.message(F.text == "📤 Рассылка")
async def handle_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    # Спрашиваем, кому отправлять
    await message.answer("📨 Отправить рассылку 'всем' зарегистрированным пользователям или указать конкретные ID? Введите 'всем' или перечислите ID через запятую.")
    
    # Устанавливаем состояние для ожидания выбора
    await state.set_state(BroadcastState.waiting_for_recipients)


# Новый обработчик для текста после команды "Рассылка"
@router.message(BroadcastState.waiting_for_recipients)
async def process_broadcast_recipients(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    # Получаем текст сообщения
    recipients_text = message.text.strip().lower()
    
    # Получаем список всех пользователей
    all_users = await db.get_all_users()
    if not all_users:
        await message.answer("📭 Нет зарегистрированных пользователей для рассылки.")
        await state.clear()
        return
    
    # Получаем список ID пользователей
    all_user_ids = [user['telegram_id'] for user in all_users]
    
    # Проверяем, отправлено ли 'всем'
    if recipients_text == 'всем':
        target_ids = all_user_ids
        # Сохраняем список ID в состояние
        await state.update_data(target_ids=target_ids)
        # Переходим к следующему шагу
        await state.set_state(BroadcastState.waiting_for_message)
        await message.answer("Введите сообщение для рассылки.")
    else:
        # Ищем список ID, введённых пользователем (например, "123, 456, 789")
        try:
            target_ids = [int(id_str.strip()) for id_str in re.split(r'[,;\s]+', recipients_text) if id_str.strip().isdigit()]
            # Фильтруем ID, оставляя только тех, кто есть в базе
            target_ids = [uid for uid in target_ids if uid in all_user_ids]
            
            if not target_ids:
                await message.answer("❌ Не найдено ни одного зарегистрированного пользователя с указанными ID.")
                return
            
            # Сохраняем список ID в состояние
            await state.update_data(target_ids=target_ids)
            # Переходим к следующему шагу
            await state.set_state(BroadcastState.waiting_for_message)
            await message.answer("Введите сообщение для рассылки.")
                
        except ValueError:
            await message.answer("❌ Некорректный формат ID. Используйте числа, разделённые запятыми, точкой с запятой или пробелами, или слово 'всем'.")
            return


# Новый обработчик для текста после команды "Рассылка"
@router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return
    
    # Получаем текст сообщения
    broadcast_text = message.text.strip()
    
    # Проверяем, не является ли сообщение командой
    if broadcast_text.startswith("/"):
        await message.answer("❌ Сообщение не должно быть командой.")
        return
    
    # Получаем список целевых ID из состояния
    data = await state.get_data()
    target_ids = data.get("target_ids", [])
    
    # Отправляем сообщение всем целевым пользователям
    success_count = 0
    for user_id in target_ids:
        try:
            await bot.send_message(user_id, broadcast_text)
            success_count += 1
        except Exception as e:
            # Логируем ошибку отправки
            print(f"[BROADCAST ERROR] Не удалось отправить сообщение пользователю {user_id}: {e}")
    
    # Подсчитываем и отправляем статистику
    total_targets = len(target_ids)
    await message.answer(f"✅ Рассылка завершена.\n\n📤 Отправлено: {success_count}/{total_targets} пользователей.")
    
    # Сбрасываем состояние
    await state.clear()