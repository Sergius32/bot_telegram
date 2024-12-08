import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import sqlite3
import time
import random

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Токен Telegram-бота
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Параметры оплаты (заглушка)
VPN_PRICE = 100  # Цена в рублях

# Подключение к SQLite базе данных
def init_db():
    conn = sqlite3.connect("subscriptions.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    expiration INTEGER
                 )''')
    conn.commit()
    conn.close()

# Функция проверки подписки
def has_valid_subscription(user_id):
    conn = sqlite3.connect("subscriptions.db")
    c = conn.cursor()
    c.execute("SELECT expiration FROM subscriptions WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        expiration = result[0]
        return expiration > time.time()
    return False

# Продление подписки
def extend_subscription(user_id, username, days):
    conn = sqlite3.connect("subscriptions.db")
    c = conn.cursor()
    expiration = int(time.time()) + days * 86400

    if has_valid_subscription(user_id):
        c.execute("UPDATE subscriptions SET expiration = expiration + ? WHERE user_id = ?", (days * 86400, user_id))
    else:
        c.execute("REPLACE INTO subscriptions (user_id, username, expiration) VALUES (?, ?, ?)", (user_id, username, expiration))

    conn.commit()
    conn.close()

# Команда /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    message = """\
Добро пожаловать в VPN-сервис! \n
Наши тарифы:\n- 7 дней за 100 рублей.\n
Для покупки нажмите на кнопку ниже.
"""
    keyboard = [[InlineKeyboardButton("Купить подписку", callback_data="buy_subscription")]]
    update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# Команда /status
def status(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    if has_valid_subscription(user_id):
        conn = sqlite3.connect("subscriptions.db")
        c = conn.cursor()
        c.execute("SELECT expiration FROM subscriptions WHERE user_id = ?", (user_id,))
        expiration = c.fetchone()[0]
        conn.close()
        remaining_days = int((expiration - time.time()) / 86400)
        update.message.reply_text(f"Ваша подписка активна. Осталось дней: {remaining_days}")
    else:
        update.message.reply_text("У вас нет активной подписки.")

# Обработка покупки
def handle_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    query.answer()

    # Симуляция оплаты (реальная оплата интегрируется через платёжные API)
    fake_payment_id = random.randint(100000, 999999)
    extend_subscription(user.id, user.username, 7)
    query.edit_message_text(
        f"Оплата успешно завершена! Ваш ID оплаты: {fake_payment_id}. Подписка активирована на 7 дней."
    )

# Главный обработчик
if __name__ == "__main__":
    init_db()

    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CallbackQueryHandler(handle_payment, pattern="buy_subscription"))

    updater.start_polling()
    updater.idle()