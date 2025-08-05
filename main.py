import os
import json
import random
from datetime import datetime
from telegram import (
    Update, ChatMember,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# تنظیمات
BLOCKED_FILE = "blocked.json"
OWNER_ID = 1841766279
OWNER_USERNAME = "@thefiblax"
GROUP_ID = -1001222208308

# لیست فحش‌ها
INSULTS = [
    "احمق", "خر", "کندذهن", "چرت", "بیشعور",
    "گاو", "شلخته", "مسخره", "مغز فندوقی", "پفیوز",
    "ابله", "نخاله", "شاسگول", "کودن", "پرت",
    "میکروب", "هویج", "بنگاه مشکل‌ساز", "مزخرف", "خرفت"
]

# --- ذخیره و لود پکیج‌های بلاک ---
def load_blocked():
    if not os.path.exists(BLOCKED_FILE):
        return []
    with open(BLOCKED_FILE, "r") as f:
        return json.load(f)

def save_blocked(blocked_packs):
    with open(BLOCKED_FILE, "w") as f:
        json.dump(blocked_packs, f)

# --- چک ادمین ---
async def is_user_admin(update: Update, user_id: int):
    member = await update.effective_chat.get_member(user_id)
    return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]

# --- هندلر استیکرها ---
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker = update.message.sticker
    blocked_packs = load_blocked()
    
    if sticker.set_name and sticker.set_name in blocked_packs:
        await update.message.delete()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_text = (
            f"📛 استیکر بلاک‌شده حذف شد!\n"
            f"👤 ارسال‌کننده: {update.effective_user.mention_html()}\n"
            f"🎨 پک: {sticker.set_name}\n"
            f"⏰ زمان: {now}\n"
            f"{OWNER_USERNAME}"
        )

        keyboard = [
            [
                InlineKeyboardButton("بیخیال", callback_data="ignore"),
                InlineKeyboardButton("فحش بده", callback_data="insult")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=report_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

# --- هندلر دکمه‌ها ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat = query.message.chat
    is_admin = await chat.get_member(user_id)
    is_admin = is_admin.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]

    if not is_admin:
        await query.edit_message_text("⛔️ فقط ادمین‌ها می‌تونن از این دکمه‌ها استفاده کنن.")
        return

    if query.data == "ignore":
        await query.edit_message_text("اوکی بیخیالش")
    elif query.data == "insult":
        insult = random.choice(INSULTS)
        await query.edit_message_text(f"{OWNER_USERNAME} گفت: {insult}")

# --- دستورات ---
async def block_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
        return
    if not context.args:
        await update.message.reply_text("استفاده: /blocksticker نام_پک_استیکر")
        return
    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name not in blocked_packs:
        blocked_packs.append(pack_name)
        save_blocked(blocked_packs)
        await update.message.reply_text(f"✅ پک {pack_name} به لیست بلاک اضافه شد.")
    else:
        await update.message.reply_text("این پک قبلاً توی لیست بلاک بوده.")

async def unblock_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
        return
    if not context.args:
        await update.message.reply_text("استفاده: /unblocksticker نام_پک_استیکر")
        return
    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name in blocked_packs:
        blocked_packs.remove(pack_name)
        save_blocked(blocked_packs)
        await update.message.reply_text(f"♻️ پک {pack_name} از لیست بلاک حذف شد.")
    else:
        await update.message.reply_text("این پک توی لیست بلاک نبود.")

async def clear_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
        return
    save_blocked([])
    await update.message.reply_text("🧹 لیست بلاک پاک شد.")

async def list_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن این لیست رو ببینن.")
        return
    blocked_packs = load_blocked()
    if not blocked_packs:
        await update.message.reply_text("❌ هیچ پکی بلاک نشده.")
    else:
        text = "📛 پک‌های بلاک‌شده:\n" + "\n".join(f"• {p}" for p in blocked_packs)
        await update.message.reply_text(text)

# --- شروع بات ---
if __name__ == "__main__":
    token = "8381798336:AAFJzwST_zeCSEooXa2pL1YP8LF_MRZuGFg"
    app = ApplicationBuilder().token(token).build()

    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("blocksticker", block_sticker))
    app.add_handler(CommandHandler("unblocksticker", unblock_sticker))
    app.add_handler(CommandHandler("clearblocked", clear_blocked))
    app.add_handler(CommandHandler("listblocked", list_blocked))

    app.run_polling()
