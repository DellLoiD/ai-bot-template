#Логика: Регистрация нового пользователя в базе данных, 
# проверка реферальных ссылок и отправка первого приветственного сообщения с кнопками.
from aiogram.fsm.state import StatesGroup, State
from states import Registration
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from loader import db, bot
from handlers.registration import CodeState
from keyboards.reply import get_main_keyboard
from keyboards.admin import get_admin_keyboard
from config import ADMIN_ID
import aiosqlite

router = Router()
 #1. Определяем этапы анкеты (универсальный класс)

# 2. Команда /start
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь администратором
    if message.from_user.id == ADMIN_ID:
        # Отправляем приветствие и устанавливаем админскую клавиатуру
        await message.answer("🔐 Добро пожаловать, администратор! Используйте меню ниже.", reply_markup=get_admin_keyboard())
        return

    # Проверяем, есть ли пользователь в базе
    user = await db.get_user(message.from_user.id)
    if user:
        # Пользователь уже зарегистрирован, предлагаем ввести код
        await message.answer("Вы уже зарегистрированы! Введите код доступа:", reply_markup=get_main_keyboard())
        # Здесь нужно перейти к состоянию ожидания кода
        await state.set_state(CodeState.waiting_for_code)
        return

    # Для пользователя, который заходит впервые (его нет в базе)
    await message.answer("Для продолжения введите код доступа:")
    await state.set_state(CodeState.waiting_for_code)

@router.message(Registration.wait_wishlist)
async def process_wishlist(message: types.Message, state: FSMContext):
    wishlist = message.text.strip()
    
    # Ограничиваем длину пожеланий до 200 символов
    if len(wishlist) > 200:
        await message.answer("❌ Слишком длинное сообщение! Пожелания не должны превышать 200 символов. Пожалуйста, сократите текст и отправьте снова:")
        return
    
    # Проверяем, что пожелание не пустое
    if not wishlist:
        await message.answer("❌ Пожелания не могут быть пустыми. Пожалуйста, напишите, что бы вы хотели получить в подарок:")
        return
    
    # Получаем все данные из состояния
    user_data = await state.get_data()
    user_id = message.from_user.id
    name = user_data.get("name")
    birthday = user_data.get("birthday")
    
    # Обновляем структуру таблицы и сохраняем данные
    await db.create_tables()
    await db.add_user(user_id, name, birthday, wishlist)
    
    await message.answer(f"🎉 Отлично, {name}! Ваши пожелания сохранены.\n\n🎁 {wishlist}")
    await state.clear() 
@router.message(Registration.wait_birthday)
async def process_birthday(message: types.Message, state: FSMContext):
    # Валидация формата даты (ДД.ММ.ГГГГ)
    import re
    date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'  # Исправлено: добавлен $ и закрыта строка
    birthday = message.text.strip()  # Исправлено: сначала получаем значение
    
    if not re.match(date_pattern, birthday):
        await message.answer("❌ Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ (например, 01.01.2000):")
        return
    
    # Получаем имя из состояния
    user_data = await state.get_data()
    name = user_data.get("name")
    
    # Логирование
    print(f"[DEBUG] Попытка сохранить данные пользователя: ID={message.from_user.id}, Имя={name}, ДР={birthday}")
    
    # Сохраняем имя и дату рождения
    await state.update_data(name=name, birthday=birthday)
    
    # Запрашиваем пожелания к подарку
    await message.answer(f"Отлично, {name}! Теперь напишите, что бы вы хотели получить в подарок (максимум 200 символов):")
    await state.set_state(Registration.wait_wishlist)