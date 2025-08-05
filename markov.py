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

OWNER_ID = 1841766279  # آیدی خودت را اینجا بگذار
ALLOWED_GROUP_ID = -1001222208308  # آیدی گروهت را اینجا بگذار
BOT_TOKEN = "8381798336:AAFJzwST_zeCSEooXa2pL1YP8LF_MRZuGFg"

# ===== لیست فحش‌ها =====
INSULTS = [
    "خفه شو.", "sybau.", "احمق بی‌مصرف.", "بی‌مغز پست.",
    "کله‌پوچ.", "سگ ولگرد.", "عقب‌مونده ذهنی.", "برو خودتو جمع کن.",
    "بی‌شرف.", "نابغه قرن.", "خر خودتی.", "کودن.", "syfm.",
    "شل مغز.", "لجن متحرک.", "برو یه فکری به حالت بکن.", "عنتر.",
    "احمق‌ترین موجود.", "لاشه متحرک.", "مغزت کجاست؟"
]

# ===== کلاس مدل مارکوف =====
class MarkovChat:
    def __init__(self, file_path=MEMORY_FILE, max_messages=5000):
        self.file_path = file_path
        self.max_messages = max_messages
        self.memory = deque(maxlen=max_messages)
        self.model = defaultdict(list)
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.memory = deque(data, maxlen=self.max_messages)
                self._rebuild_model()

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(list(self.memory), f, ensure_ascii=False)

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

        length = random.randint(5, 10) if random.random() < 0.3 else random.randint(15, 25)

        for _ in range(length - 2):
            key = (result[-2], result[-1])
            next_words = self.model.get(key)
            if not next_words:
                break
            result.append(random.choice(next_words))

        return " ".join(result)

    def remove_user_messages(self, user_id: int, user_messages_map):
        # user_messages_map: dict[user_id] = list of messages
        # حذف پیام‌هایی که از یک user_id هست
        removed_count = 0
        new_memory = deque(maxlen=self.max_messages)
        for msg_user_id, msg_text in user_messages_map:
            if msg_user_id != user_id:
                new_memory.append(msg_text)
            else:
                removed_count += 1
        self.memory = new_memory
        self._rebuild_model()
        self.save()
        return removed_count

# ===== مدیریت بلاک استیکر =====
def load_blocked():
    if not os.path.exists(BLOCKED_FILE):
        return []
    with open(BLOCKED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_blocked(blocked_packs):
    with open(BLOCKED_FILE, "w", encoding="utf-8") as f:
        json.dump(blocked_packs, f, ensure_ascii=False)

# ===== بررسی ادمین بودن کاربر =====
async def is_user_admin(update: Update, user_id: int) -> bool:
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

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
        text = f"{admin_link} کاربر {user_link} (آیدی: {user.id}) یک استیکر بلاک‌شده فرستاد، ولی حذف نشد چون ادمینه."
        await context.bot.send_message(chat_id=ALLOWED_GROUP_ID, text=text, parse_mode="Markdown")
    else:
        await update.message.delete()
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("بیخیال", callback_data=f"ignore:{user.id}"),
                                         InlineKeyboardButton("فحش بده", callback_data=f"insult:{user.id}:{user.username or user.full_name}")]])
        text = f"{admin_link} کاربر {user_link} (آیدی: {user.id}) یک استیکر بلاک‌شده فرستاد و حذف شد."
        await context.bot.send_message(chat_id=ALLOWED_GROUP_ID, text=text, reply_markup=keyboard, parse_mode="Markdown")

# ===== هندل دکمه‌ها =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_chat.id != ALLOWED_GROUP_ID:
        return

    is_admin = await is_user_admin(update, query.from_user.id)
    if not is_admin:
        await query.answer("⛔ فقط ادمین‌ها می‌تونن از این دکمه استفاده کنن.", show_alert=True)
        return

    data = query.data.split(":")
    action = data[0]

    if action == "ignore":
        await query.edit_message_text("اوکی، بیخیالش.")
    elif action == "insult":
        username = data[2]
        insult = random.choice(INSULTS)
        await query.edit_message_text(f"کاربر {username} {insult}")

# ===== مدیریت و یادگیری پیام‌ها =====
markov = MarkovChat()
AUTO_CHAT = True  # حالت چت خودکار روشن

# برای ذخیره پیام‌ها همراه آیدی کاربر
user_messages_map = deque(maxlen=5000)  # هر عضو: (user_id, text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_CHAT
    message = update.message
    chat_id = message.chat.id

    if chat_id != ALLOWED_GROUP_ID:
        return

    text = message.text
    user = update.effective_user

    if user.is_bot or not text:
        return

    # ذخیره پیام برای مارکوف به همراه آیدی کاربر
    user_messages_map.append((user.id, text))

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

# ===== دستورات مارکوف (فقط ادمین‌ها) =====
async def toggle_chatter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این کارو انجام بدن.")
    global AUTO_CHAT
    AUTO_CHAT = not AUTO_CHAT
    state = "روشن" if AUTO_CHAT else "خاموش"
    await update.message.reply_text(f"حالت چت خودکار: {state}")

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این کارو انجام بدن.")
    markov.memory.clear()
    markov.model.clear()
    user_messages_map.clear()
    markov.save()
    await update.message.reply_text("🧹 حافظه مارکوف پاک شد.")

async def generate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این کارو انجام بدن.")
    response = markov.generate()
    await update.message.reply_text(response if response else "❌ هنوز حافظه‌ای برای تولید متن وجود نداره.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این کارو انجام بدن.")
    await update.message.reply_text(f"تعداد پیام‌های ذخیره‌شده: {len(markov.memory)}")

async def remove_memory_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این کارو انجام بدن.")
    if not context.args:
        return await update.message.reply_text("لطفاً آیدی عددی کاربر مورد نظر را بعد از دستور وارد کنید.\nمثال: /removememoryfrom 123456789")
    try:
        user_id_to_remove = int(context.args[0])
    except:
        return await update.message.reply_text("آیدی وارد شده معتبر نیست.")
    removed_count = 0
    global user_messages_map
    # حذف پیام‌های اون کاربر از لیست پیام‌ها و مدل مارکوف
    new_map = deque()
    for uid, msg_text in user_messages_map:
        if uid != user_id_to_remove:
            new_map.append((uid, msg_text))
        else:
            removed_count += 1
    user_messages_map = new_map
    markov.memory = deque([msg for uid, msg in user_messages_map], maxlen=markov.max_messages)
    markov._rebuild_model()
    markov.save()
    await update.message.reply_text(f"پیام‌های یادگرفته شده از کاربر با آیدی {user_id_to_remove} پاک شد.\nتعداد پیام‌های حذف شده: {removed_count}")

# ===== دستورات استیکر (فقط ادمین‌ها) =====
async def block_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
    if not context.args:
        return await update.message.reply_text("لطفاً نام پک استیکر را بعد از دستور وارد کنید.\nمثال: /blocksticker MyPackName")
    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name in blocked_packs:
        return await update.message.reply_text(f"این پک قبلاً بلاک شده است: `{pack_name}`", parse_mode="Markdown")
    blocked_packs.append(pack_name)
    save_blocked(blocked_packs)
    await update.message.reply_text(f"پک `{pack_name}` بلاک شد.", parse_mode="Markdown")

async def unblock_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
    if not context.args:
        return await update.message.reply_text("لطفاً نام پک استیکر را بعد از دستور وارد کنید.\nمثال: /unblocksticker MyPackName")
    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name not in blocked_packs:
        return await update.message.reply_text(f"این پک بلاک نیست: `{pack_name}`", parse_mode="Markdown")
    blocked_packs.remove(pack_name)
    save_blocked(blocked_packs)
    await update.message.reply_text(f"پک `{pack_name}` آنبلاک شد.", parse_mode="Markdown")

# ===== ثبت دستورات در بات‌فادر =====
# togglechatter - روشن یا خاموش کردن حالت چت خودکار (پاسخ تصادفی)
# clearmemory - پاک کردن کل حافظه یادگیری مارکوف
# generate - تولید یک جمله جدید با مدل مارکوف
# stats - نمایش آمار حافظه
# blocksticker - بلاک کردن پک استیکر خاص
# unblocksticker - آنبلاک کردن پک استیکر خاص
# removememoryfrom - حذف پیام‌های یادگرفته شده از یک کاربر خاص

# ===== اجرای بات =====
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # هندل پیام‌های متنی
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    # هندل استیکر
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

    # هندل دکمه‌های اینلاین
    app.add_handler(CallbackQueryHandler(button_handler))

    # کامندها
    app.add_handler(CommandHandler("togglechatter", toggle_chatter))
    app.add_handler(CommandHandler("clearmemory", clear_memory))
    app.add_handler(CommandHandler("generate", generate_text))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("blocksticker", block_sticker))
    app.add_handler(CommandHandler("unblocksticker", unblock_sticker))
    app.add_handler(CommandHandler("removememoryfrom", remove_memory_from))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
