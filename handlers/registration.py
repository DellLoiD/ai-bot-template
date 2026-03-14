#проверяет код доступа, который пользователь прислал боту

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from database.methods import check_activation_code, use_code
from loader import db
from config import ADMIN_ID
from states import CodeState, Registration  # Импортируем оба класса состояний

router = Router()

@router.message(F.text == "🔑 Ввести код")
async def enter_code(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь администратором
    if message.from_user.id == ADMIN_ID:
        await message.answer("❌ Администратору не нужно вводить код доступа.")
        return
    
    await message.answer("Введите ваш код доступа:")
    await state.set_state(CodeState.waiting_for_code)

@router.message(CodeState.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь администратором
    if message.from_user.id == ADMIN_ID:
        await message.answer("❌ Администратору не нужно вводить код доступа.")
        return
    
    code = message.text.strip()
    print(f"[DEBUG] Пользователь ввел код: '{code}'")
    if await check_activation_code(code):
        # Код верный, помечаем его как использованный
        await use_code(code, message.from_user.id)
        # И только потом начинаем процесс регистрации
        await message.answer("✅ Код принят! Начнем регистрацию. Введите свое имя:")
        print("[DEBUG] Переход к состоянию ввода имени: wait_name")
        await state.set_state(Registration.wait_name)
        return  # Важно выйти, чтобы не упало в else
    else:
        await message.answer("❌ Неверный код. Попробуйте еще раз или обратитесь к администратору.")