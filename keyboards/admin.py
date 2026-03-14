#Специальные кнопки, которые видит только заказчик или модератор.
#Состав: «Выгрузить Excel», «Разослать уведомления», «Статистика за 30 дней».
#Особенность: Часто эти кнопки ведут в скрытые разделы управления ботом.

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Функция для создания клавиатуры админа (постоянная, под строкой ввода)
def get_admin_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📋 Все пользователи"), KeyboardButton(text="📊 Выгрузить Excel")],
        [KeyboardButton(text="📤 Рассылка"), KeyboardButton(text="🔑 Сгенерировать коды доступа")],
        [KeyboardButton(text="🔑 Коды доступа")],
        [KeyboardButton(text="🗑️ Удалить пользователя")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, selective=True)