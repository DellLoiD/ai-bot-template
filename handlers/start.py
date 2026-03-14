#Логика: Регистрация нового пользователя в базе данных, 
# проверка реферальных ссылок и отправка первого приветственного сообщения с кнопками.
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from loader import db, bot
from handlers.registration import CodeState
from database.methods import use_code


from keyboards.reply import get_main_keyboard
from keyboards.admin import get_admin_keyboard
from config import ADMIN_ID

# 1. Определяем этапы анкеты (универсальный класс)
class Registration(StatesGroup):
    wait_name = State()      # Ждем имя
    wait_birthday = State()  # Ждем дату рождения
    wait_extra = State()     # Ждем доп. инфо (например, пожелания)

router = Router()

# 2. Команда /start
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь администратором
    if message.from_user.id == ADMIN_ID:
        # Отправляем приветствие и устанавливаем админскую клавиатуру
        await message.answer("🔐 Добро пожаловать, администратор! Используйте меню ниже.", reply_markup=get_admin_keyboard())
        return

    # Для обычного пользователя показываем только кнопку проверки регистрации
    await message.answer("Нажмите кнопку ниже, чтобы проверить регистрацию.", reply_markup=get_main_keyboard())

# 3. Ловим имя и переходим к дате
@router.message(Registration.wait_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    
    # Проверка на валидность имени: только буквы и пробелы
    if not name.replace(' ', '').isalpha():
        await message.answer("❌ Имя должно содержать только буквы. Пожалуйста, введите корректное имя:")
        return
    
    await state.update_data(name=name) # Сохраняем имя во временную память
    print(f"[DEBUG] Имя пользователя '{name}' сохранено. Переход к вводу даты рождения.")
    await message.answer(f"Приятно познакомиться, {name}! Теперь введите дату рождения (ДД.ММ.ГГГГ):")
    await state.set_state(Registration.wait_birthday)

# 4. Ловим дату и завершаем (или идем дальше)
@router.message(Registration.wait_birthday)
async def process_birthday(message: types.Message, state: FSMContext):
    # Валидация формата даты (ДД.ММ.ГГГГ)
    import re
    date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
    birthday = message.text.strip()
    
    if not re.match(date_pattern, birthday):
        await message.answer("❌ Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ (например, 01.01.2000):")
        return
    
    user_data = await state.get_data() # Достаем всё, что сохранили ранее
    name = user_data.get("name")
    
    # Логирование перед сохранением
    print(f"[DEBUG] Попытка сохранить данные пользователя: ID={message.from_user.id}, Имя={name}, ДР={birthday}")
    
    # СОХРАНЯЕМ В БАЗУ
    await db.add_user(message.from_user.id, name, birthday)
    
    await message.answer(f"Данные сохранены! Теперь я знаю, что у {name} праздник {birthday}.")
    await state.clear()
    
    # Логирование завершения
    print(f"[DEBUG] Регистрация завершена для пользователя: {name}")
    
    # Отправляем сообщение с клавиатурой для пользователя
    await message.answer(f"Готово! {name}, я запомнил твой день рождения: {birthday}", reply_markup=get_main_keyboard())
    await state.clear() # Очищаем состояния