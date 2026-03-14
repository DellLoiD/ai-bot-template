#Это «постоянные» кнопки, которые висят внизу экрана.
#Состав: Кнопки «Мой прогресс», «Поддержка», «Оставить заявку».
#Особенность: Они отправляют в чат обычный текст. Бот реагирует на них как на текстовые команды.

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Функция для создания постоянной клавиатуры ��тветов
def get_main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📅 Проверить регистрацию")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)