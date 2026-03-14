#Теперь есть один главный файл (main.py), который запускает процесс, 
# и один файл ресурсов (loader.py), из которого все остальные берут настройки.
# loader.py
import logging
from aiogram import Bot, Dispatcher
from database.data import Database
from config import BOT_TOKEN

# Создаём объекты
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

