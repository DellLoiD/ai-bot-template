import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_NAME = os.getenv("DB_NAME")
WELCOME_TEXT = os.getenv("WELCOME_TEXT")
BIRTHDAY_ALERT_DAYS = int(os.getenv("BIRTHDAY_ALERT_DAYS", 7))