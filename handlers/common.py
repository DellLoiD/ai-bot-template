#Примеры: Команды /help (помощь), /settings (настройки) 
# или /cancel (отмена текущего действия и возврат в главное меню).
# Обработка нажатий на кнопки клавиатуры (ReplyKeyboard)

from aiogram import Router, types
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.context import FSMContext

router = Router()

# Импортируем необходимые компоненты для генерации кодов
from utils.code_generator import CodeGenerator
from loader import db
from config import ADMIN_ID
from handlers.registration import CodeState

@router.message(Command("help"))
async def help_command(message: types.Message):
    # Импортируем клавиатуру
    from keyboards.reply import get_main_keyboard
    
    help_text = "Добро пожаловать в помощник бота!\n\nДоступные команды:\n/help - Показать это сообщение\n/settings - Настройки бота\n/cancel - Отменить текущее действие\n\nВы также можете использовать кнопки в меню для навигации."
    await message.answer(help_text, reply_markup=get_main_keyboard())

@router.message(Command("settings"))
async def settings_command(message: types.Message):
    # Импортируем клавиатуру
    from keyboards.reply import get_main_keyboard
    await message.answer("Настройки бота", reply_markup=get_main_keyboard())

@router.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    await state.clear()
    # Импортируем клавиатуру
    from keyboards.reply import get_main_keyboard
    await message.answer("Действие отменено", reply_markup=get_main_keyboard())

# Проверка админа (копия из admin.py для автономности)
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_ID

# Обработка нажатия на кнопку "🔑 Сгенерировать коды доступа"
@router.message(F.text == "🔑 Сгенерировать коды доступа")
async def handle_generate_codes_button(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Доступ запрещён.")
        return

    code_gen = CodeGenerator(db)
    try:
        codes = await code_gen.generate_and_save_codes(10)
        codes_list = "\n".join(f"🔑 {code}" for code in codes)
        response = f"✅ Сгенерировано 10 кодов доступа:\n\n{codes_list}"
        await message.answer(response)
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации кодов: {e}")


@router.message(F.text == "📅 Проверить регистрацию")
async def handle_check_registration(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь администратором
    if message.from_user.id == ADMIN_ID:
        return  # Админ обрабатывается в другом месте

    # Проверяем, есть ли пользователь в базе
    user = await db.get_user(message.from_user.id)
    if user:
        # Пользователь найден, показываем его данные
        await message.answer(f"✅ Вы зарегистрированы в боте:\n\n👤 Имя: {user['name']}\n🎂 Дата рождения: {user['birthday']}")
    else:
        # Пользователь не найден, запрашиваем код доступа
        await message.answer("❌ Вы не зарегистрированы. Пожалуйста, введите код доступа:")
        await state.set_state(CodeState.waiting_for_code)