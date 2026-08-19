import random
import string
import asyncio
import os
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== НАСТРОЙКИ =====
TOKEN = "8842960290:AAEbXbMGLDXeFjX6PzXRS0AJqJ1RQGN4z48"
CHANNEL_USERNAME = "@Durov_poul"
COOLDOWN_SECONDS = 30
GENERATION_COUNT = 10
user_last_request = {}

# ===== ФУНКЦИИ БОТА =====
def generate_random_username(length: int) -> str:
    return ''.join(random.choices(string.ascii_lowercase, k=length))

async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ('member', 'administrator', 'creator')
    except:
        return False

async def check_username(username: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        await context.bot.get_chat(f"@{username}")
        return False
    except Exception:
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 5 знаков", callback_data="5")],
        [InlineKeyboardButton("🔍 6 знаков", callback_data="6")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Привет, этот бот абсолютно бесплатный.\n\n"
        "Для поддержки автора, пожалуйста, подпишитесь на канал @Durov_poul. "
        "Будем вам признательны! 🫶\n\n"
        "Выберите длину ника:",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    length = int(query.data)
    
    if not await is_subscribed(user_id, context):
        await query.edit_message_text(
            f"❌ Чтобы продолжить, подпишитесь на канал {CHANNEL_USERNAME}.\n"
            "После подписки нажмите /start заново."
        )
        return
    
    now = datetime.now()
    if user_id in user_last_request:
        time_passed = (now - user_last_request[user_id]).total_seconds()
        if time_passed < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - time_passed)
            await query.edit_message_text(f"⏳ Подождите ещё {remaining} секунд.")
            return
    
    user_last_request[user_id] = now
    await query.edit_message_text(f"🔍 Ищу {GENERATION_COUNT} свободных {length}-значных имён...")
    
    found_names = []
    attempts = 0
    
    while len(found_names) < GENERATION_COUNT:
        attempts += 1
        username = generate_random_username(length)
        if username in found_names:
            continue
        if await check_username(username, context):
            found_names.append(username)
            if len(found_names) % 2 == 0:
                await context.bot.send_message(user_id, f"✅ Найдено: @{username}")
        await asyncio.sleep(0.3)
    
    names_list = "\n".join([f"@{name}" for name in found_names])
    await context.bot.send_message(
        user_id,
        f"🎉 Найдено {len(found_names)} имён:\n\n{names_list}\n\nВсего проверено: {attempts} вариантов."
    )

# ===== ВЕБ-СЕРВЕР ДЛЯ ХОСТИНГА (чтобы не вырубался) =====
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Bot is active and running!"

def run_telegram_bot():
    print("🤖 Бот запущен!")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()

if __name__ == '__main__':
    # Запускаем телеграм-бота в фоновом потоке
    t = threading.Thread(target=run_telegram_bot)
    t.daemon = True
    t.start()

    # Запускаем веб-сервер Flask
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host='0.0.0.0', port=port)
