import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
import time
import random
import logging

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Извлекаем токен из переменной окружения

# Параметры оплаты (заглушка)
VPN_PRICE = 100  # Цена в рублях

# Подключение к SQLite базе данных с использованием контекстного менеджера
def init_db():
    with sqlite3.connect("subscriptions.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        expiration INTEGER
                     )''')
        conn.commit()

# Функция проверки подписки
def has_valid_subscription(user_id):
    with sqlite3.connect("subscriptions.db") as conn:
        c = conn.cursor()
        c.execute("SELECT expiration FROM subscriptions WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            expiration = result[0]
            return expiration > time.time()
    return False

# Продление подписки
def extend_subscription(user_id, username, days):
    with sqlite3.connect("subscriptions.db") as conn:
        c = conn.cursor()
        expiration = int(time.time()) + days * 86400

        if has_valid_subscription(user_id):
            c.execute("UPDATE subscriptions SET expiration = expiration + ? WHERE user_id = ?", (days * 86400, user_id))
        else:
            c.execute("REPLACE INTO subscriptions (user_id, username, expiration) VALUES (?, ?, ?)", (user_id, username, expiration))

        conn.commit()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = "Добро пожаловать в VPN-сервис! Выберите действие ниже."
    keyboard = ReplyKeyboardMarkup([["Мои подписки", "Покупка"]], resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=keyboard)

# Обработка нажатия на кнопку "Мои подписки"
async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if has_valid_subscription(user.id):
        with sqlite3.connect("subscriptions.db") as conn:
            c = conn.cursor()
            c.execute("SELECT expiration FROM subscriptions WHERE user_id = ?", (user.id,))
            expiration = c.fetchone()[0]
            remaining_days = int((expiration - time.time()) / 86400)
        await update.message.reply_text(f"Ваша подписка активна. Осталось дней: {remaining_days}")
    else:
        await update.message.reply_text("У вас нет активной подписки.")

# Обработка нажатия на кнопку "Покупка"
async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Симуляция оплаты (реальная оплата интегрируется через платёжные API)
    fake_payment_id = random.randint(100000, 999999)
    extend_subscription(user.id, user.username, 7)
    await update.message.reply_text(
        f"Оплата успешно завершена! Ваш ID оплаты: {fake_payment_id}. Подписка активирована на 7 дней."
    )

# Обработчик текстовых сообщений (для кнопок "Мои подписки" и "Покупка")
async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Мои подписки":
        await my_subscriptions(update, context)
    elif update.message.text == "Покупка":
        await buy_subscription(update, context)

# Главный обработчик
if __name__ == "__main__":
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("Мои подписки"), handle_button_press))  # Обработка кнопки "Мои подписки"
    app.add_handler(MessageHandler(filters.Text("Покупка"), handle_button_press))  # Обработка кнопки "Покупка"

    try:
        app.run_polling()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
