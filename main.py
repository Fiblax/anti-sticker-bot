import os
import json
import random
from telegram import (
    Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ===== تنظیمات =====
BLOCKED_FILE = "blocked.json"
OWNER_ID = 1841766279  # آیدی عددی شما
ALLOWED_GROUP_ID = -1001222208308  # آیدی گروه
BOT_TOKEN = "8381798336:AAFJzwST_zeCSEooXa2pL1YP8LF_MRZuGFg"  # توکن ربات

# ===== لیست فحش‌ها =====
INSULTS = [
    "خفه شو.", "sybau.", "احمق بی‌مصرف.", "بی‌مغز پست.",
    "کله‌پوچ.", "سگ ولگرد.", "عقب‌مونده ذهنی.", "برو خودتو جمع کن.",
    "بی‌شرف.", "نابغه قرن.", "خر خودتی.", "کودن.", "syfm.",
    "شل مغز.", "لجن متحرک.", "برو یه فکری به حالت بکن.", "عنتر.",
    "احمق‌ترین موجود.", "لاشه متحرک.", "مغزت کجاست؟"
]

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
        # ادمین → استیکر حذف نمی‌شود
        text = f"{admin_link} کاربر {user_link} (آیدی: {user.id}) :(یک استیکر بلاک‌شده فرستاد، ولی چون ادمینه حذف نشد."
        await context.bot.send_message(
            chat_id=ALLOWED_GROUP_ID,
            text=text,
            parse_mode="Markdown"
        )
    else:
        # کاربر عادی → استیکر حذف می‌شود و دکمه اضافه می‌شود
        await update.message.delete()

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("بیخیال", callback_data=f"ignore:{user.id}"),
            InlineKeyboardButton("فحش بده", callback_data=f"insult:{user.id}:{user.username or user.full_name}")
        ]])

        text = f"{admin_link} کاربر {user_link} (آیدی: {user.id}) یک استیکر بلاک‌شده فرستاد و حذف شد."
        await context.bot.send_message(
            chat_id=ALLOWED_GROUP_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

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

# ===== دستورات =====
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
        await update.message.reply_text("این پک قبلاً بلاک بوده.")

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
        await update.message.reply_text(f"❎ پک {pack_name} از لیست بلاک حذف شد.")
    else:
        await update.message.reply_text("این پک توی لیست بلاک نبود.")

async def clear_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
        return
    save_blocked([])
    await update.message.reply_text("🧹 تمام پک‌های بلاک پاک شدند.")

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

# ===== شروع ربات =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("blocksticker", block_sticker))
    app.add_handler(CommandHandler("unblocksticker", unblock_sticker))
    app.add_handler(CommandHandler("clearblocked", clear_blocked))
    app.add_handler(CommandHandler("listblocked", list_blocked))

    app.run_polling()
