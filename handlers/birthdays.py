import asyncio
from datetime import datetime, timedelta
from aiogram import types
from loader import bot, db, ADMIN_ID
from config import BIRTHDAY_ALERT_DAYS


async def check_upcoming_birthdays():
    """Проверяет ближайшие дни рождения и отправляет уведомление администратору."""
    while True:
        try:
            # Получаем всех пользователей из базы данных
            users = await db.get_all_users()
            
            if not users:
                await asyncio.sleep(3600)  # Проверяем раз в час, если нет пользователей
                continue
            
            # Текущая дата
            today = datetime.now().date()
            alert_date = today + timedelta(days=BIRTHDAY_ALERT_DAYS)
            
            # Форматируем месяц и день для сравнения (ДД.ММ)
            alert_day_month = alert_date.strftime("%d.%m")
            
            # Ищем пользователей, у которых день рождения через BIRTHDAY_ALERT_DAYS дней
            upcoming_users = []
            for user in users:
                birthday = user.get("birthday")
                if birthday and len(birthday) >= 5:  # Проверяем, что дата не пустая и имеет минимум 5 символов (ДД.ММ)
                    # Сравниваем только день и месяц
                    if birthday[:5] == alert_day_month:
                        upcoming_users.append(user)
            
            # Если есть пользователи с приближающимся днём рождения, отправляем уведомление администратору
            if upcoming_users:
                message = f"🎉 Через {BIRTHDAY_ALERT_DAYS} дней отмечают день рождения:\n\n"
                for user in upcoming_users:
                    name = user.get("name", "Неизвестно")
                    birthday = user.get("birthday", "Неизвестно")
                    wishlist = user.get("wishlist", "Не указано")
                    message += f"👤 {name} (ДР: {birthday})\n🎁 Пожелания: {wishlist}\n\n"
                
                try:
                    await bot.send_message(ADMIN_ID, message)
                except Exception as e:
                    print(f"[ERROR] Не удалось отправить сообщение администратору {ADMIN_ID}: {e}")
            
            # Ждем 24 часа перед следующей проверкой
            await asyncio.sleep(86400)
            
        except Exception as e:
            print(f"[ERROR] Ошибка в проверке дней рождения: {e}")
            await asyncio.sleep(3600)  # В случае ошибки ждем час и пробуем снова