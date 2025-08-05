import os
import json
import random
from collections import defaultdict, deque
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ===== تنظیمات =====
BLOCKED_FILE = "blocked.json"
MEMORY_FILE = "memory.json"
OWNER_ID = 1841766279
ALLOWED_GROUP_ID = -1001222208308
BOT_TOKEN = "8381798336:AAFJzwST_zeCSEooXa2pL1YP8LF_MRZuGFg"

# ===== لیست فحش‌ها =====
INSULTS = [
    "خفه شو.", "sybau.", "احمق بی‌مصرف.", "بی‌مغز پست.",
    "کله‌پوچ.", "سگ ولگرد.", "عقب‌مونده ذهنی.", "برو خودتو جمع کن.",
    "بی‌شرف.", "نابغه قرن.", "خر خودتی.", "کودن.", "syfm.",
    "شل مغز.", "لجن متحرک.", "برو یه فکری به حالت بکن.", "عنتر.",
    "احمق‌ترین موجود.", "لاشه متحرک.", "مغزت کجاست؟"
]

# ===== مارکوف تریگرام =====
class MarkovChat:
    def __init__(self, file_path=MEMORY_FILE, max_messages=5000):
        self.file_path = file_path
        self.max_messages = max_messages
        self.memory = deque(maxlen=max_messages)
        self.model = defaultdict(list)
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                self.memory = deque(json.load(f), maxlen=self.max_messages)
                self._rebuild_model()

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(list(self.memory), f)

    def _rebuild_model(self):
        self.model.clear()
        for msg in self.memory:
            words = msg.split()
            if len(words) < 3:
                continue
            for i in range(len(words) - 2):
                key = (words[i], words[i+1])
                self.model[key].append(words[i+2])

    def learn(self, message):
        self.memory.append(message)
        words = message.split()
        if len(words) < 3:
            return
        for i in range(len(words) - 2):
            key = (words[i], words[i+1])
            self.model[key].append(words[i+2])
        self.save()

    def generate(self):
        if not self.model:
            return None
        start = random.choice(list(self.model.keys()))
        result = [start[0], start[1]]

        # 70٪ بلند، 30٪ کوتاه
        length = random.randint(5, 10) if random.random() < 0.3 else random.randint(15, 25)

        for _ in range(length - 2):
            key = (result[-2], result[-1])
            next_words = self.model.get(key)
            if not next_words:
                break
            result.append(random.choice(next_words))

        return " ".join(result)

markov = MarkovChat()
AUTO_CHAT = True

# ===== مدیریت بلاک =====
def load_blocked():
    if not os.path.exists(BLOCKED_FILE):
        return []
    with open(BLOCKED_FILE, "r") as f:
        return json.load(f)

def save_blocked(blocked_packs):
    with open(BLOCKED_FILE, "w") as f:
        json.dump(blocked_packs, f)

async def is_user_admin(update: Update, user_id: int):
    member = await update.effective_chat.get_member(user_id)
    return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]

# ===== مدیریت استیکر =====
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_GROUP_ID:
        return

    sticker = update.message.sticker
    blocked_packs = load_blocked()

    if not sticker.set_name or sticker.set_name not in blocked_packs:
        return

    user = update.effective_user
    is_admin = await is_user_admin(update, user.id)

    admin_link = f"[ادمین](tg://user?id={OWNER_ID})"
    user_link = f"[{user.full_name}](tg://user?id={user.id})"

    if is_admin:
        text = f"{admin_link} کاربر {user_link} (آیدی: {user.id}) یک استیکر بلاک‌شده فرستاد، ولی چون ادمینه حذف نشد."
        await context.bot.send_message(chat_id=ALLOWED_GROUP_ID, text=text, parse_mode="Markdown")
    else:
        await update.message.delete()
        keyboard = InlineKeyboardMarkup([[ 
            InlineKeyboardButton("بیخیال", callback_data=f"ignore:{user.id}"),
            InlineKeyboardButton("فحش بده", callback_data=f"insult:{user.id}:{user.username or user.full_name}")
        ]])
        text = f"{admin_link} کاربر {user_link} (آیدی: {user.id}) یک استیکر بلاک‌شده فرستاد و حذف شد."
        await context.bot.send_message(chat_id=ALLOWED_GROUP_ID, text=text, reply_markup=keyboard, parse_mode="Markdown")

# ===== دکمه‌های شیشه‌ای =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_chat.id != ALLOWED_GROUP_ID:
        return

    is_admin = await is_user_admin(update, query.from_user.id)
    data = query.data.split(":")
    action = data[0]

    if not is_admin:
        await query.answer("⛔ فقط ادمین‌ها می‌تونن از این دکمه استفاده کنن.", show_alert=True)
        return

    if action == "ignore":
        await query.edit_message_text("اوکی، بیخیالش.")
    elif action == "insult":
        username = data[2]
        insult = random.choice(INSULTS)
        await query.edit_message_text(f"کاربر {username} {insult}")

# ===== مارکوف: یادگیری و پاسخ =====
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_CHAT
    message = update.message
    chat_id = message.chat.id

    if chat_id != ALLOWED_GROUP_ID:
        return

    text = message.text
    user = update.effective_user

    if not user.is_bot:
        markov.learn(text)

    must_reply = (
        message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id
    ) or (
        f"@{context.bot.username}" in text
    )
    random_reply = AUTO_CHAT and random.random() < 0.1

    if must_reply or random_reply:
        response = markov.generate()
        if response:
            if must_reply:
                await message.reply_text(response)
            else:
                await context.bot.send_message(chat_id=chat_id, text=response)

# ===== دستورات مارکوف =====
async def toggle_chatter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_CHAT
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این کارو انجام بدن.")
    AUTO_CHAT = not AUTO_CHAT
    state = "روشن" if AUTO_CHAT else "خاموش"
    await update.message.reply_text(f"حالت چت خودکار: {state}")

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این کارو انجام بدن.")
    markov.memory.clear()
    markov.model.clear()
    markov.save()
    await update.message.reply_text("🧹 حافظه مارکوف پاک شد.")

# ===== دستورات استیکر =====
async def block_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
    if not context.args:
        return await update.message.reply_text("استفاده: /blocksticker نام_پک_استیکر")
    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name not in blocked_packs:
        blocked_packs.append(pack_name)
        save_blocked(blocked_packs)
        await update.message.reply_text(f"✅ پک {pack_name} به لیست بلاک اضافه شد.")
    else:
        await update.message.reply_text("این پک قبلاً بلاک بوده.")

async def unblock_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
    if not context.args:
        return await update.message.reply_text("استفاده: /unblocksticker نام_پک_استیکر")
    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name in blocked_packs:
        blocked_packs.remove(pack_name)
        save_blocked(blocked_packs)
        await update.message.reply_text(f"❎ پک {pack_name} از لیست بلاک حذف شد.")
    else:
        await update.message.reply_text("این پک توی لیست بلاک نبود.")

async def clear_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
    save_blocked([])
    await update.message.reply_text("🧹 تمام پک‌های بلاک پاک شدند.")

async def list_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن این لیست رو ببینن.")
    blocked_packs = load_blocked()
    if not blocked_packs:
        await update.message.reply_text("❌ هیچ پکی بلاک نشده.")
    else:
        text = "📛 پک‌های بلاک‌شده:\n" + "\n".join(f"• {p}" for p in blocked_packs)
        await update.message.reply_text(text)

# ===== شروع ربات =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("blocksticker", block_sticker))
    app.add_handler(CommandHandler("unblocksticker", unblock_sticker))
    app.add_handler(CommandHandler("clearblocked", clear_blocked))
    app.add_handler(CommandHandler("listblocked", list_blocked))
    app.add_handler(CommandHandler("togglechatter", toggle_chatter))
    app.add_handler(CommandHandler("clearmemory", clear_memory))

    app.run_polling()
