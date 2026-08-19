import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== НАСТРОЙКИ =====
TOKEN = "8842960290:AAEbXbMGLDXeFjX6PzXRS0AJqJ1RQGN4z48"
CHANNEL_USERNAME = "@Durov_poul"
COOLDOWN_SECONDS = 30
GENERATION_COUNT = 10
user_last_request = {}

# ===== НАСТОЯЩИЙ СЛОВАРЬ АНГЛИЙСКИХ СЛОВ =====
ENGLISH_WORDS = [
    "apple", "happy", "sunny", "bright", "cloud", "ocean", "river", "storm", 
    "moon", "star", "light", "heart", "dream", "world", "peace", "brain", 
    "smart", "quick", "slow", "fast", "tall", "short", "big", "small", 
    "real", "nice", "cool", "warm", "cold", "new", "old", "young", 
    "urban", "rural", "elite", "prime", "logic", "magic", "royal", "queen", 
    "king", "city", "town", "village", "forum", "miner", "diver", "power", 
    "happy", "angry", "good", "bad", "free", "safe", "wild", "wise", 
    "mad", "rad", "top", "mix", "box", "cat", "dog", "fox", 
    "sun", "sky", "fire", "water", "earth", "wind", "rain", "snow", 
    "ice", "gold", "silver", "iron", "steel", "wood", "stone", "rock", 
    "wave", "lake", "sea", "bay", "cape", "isle", "land", "love", 
    "hope", "faith", "trust", "noble", "hero", "epic", "fame", "glory", 
    "honor", "valor", "pride", "grace", "charm", "smile", "laugh", "joy", 
    "bliss", "calm", "serene", "quiet", "still", "witty", "genius", "mega", 
    "ultra", "super", "hyper", "max", "pro", "best", "great", "fine", 
    "cool", "worst", "legend", "myth", "idea", "zone"
]

# ===== ФУНКЦИИ БОТА =====
def get_random_word(length: int) -> str:
    candidates = [w for w in ENGLISH_WORDS if len(w) == length]
    if candidates:
        return random.choice(candidates)
    return None

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
        [InlineKeyboardButton("🔍 6 знаков", callback_data="6")],
        [InlineKeyboardButton("📖 Слова (любая длина)", callback_data="words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Привет, этот бот абсолютно бесплатный.\n\n"
        "Для поддержки автора, пожалуйста, подпишитесь на канал @Durov_poul. "
        "Будем вам признательны! 🫶\n\n"
        "Выберите режим поиска:",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
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
    
    # Определяем, что ищем
    word_mode = False
    length = 0
    
    if data == "words":
        word_mode = True
        length = random.choice([4, 5, 6, 7, 8])  # случайная длина
        await query.edit_message_text(f"📖 Ищу свободные английские слова (длина {length})...")
    else:
        length = int(data)
        await query.edit_message_text(f"🔍 Ищу {GENERATION_COUNT} свободных {length}-значных имён...")
    
    found_names = []
    attempts = 0
    
    while len(found_names) < GENERATION_COUNT:
        attempts += 1
        
        if word_mode:
            username = get_random_word(length)
            if username is None:
                continue
        else:
            username = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))
        
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

# ===== ЗАПУСК =====
print("🤖 Бот запущен!")
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_click))
app.run_polling()