import os
import json
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)

BLOCKED_FILE = "blocked.json"

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

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker = update.message.sticker
    blocked_packs = load_blocked()
    if sticker.set_name and sticker.set_name in blocked_packs:
        await update.message.delete()

async def block_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
        return

    if not context.args:
        await update.message.reply_text("استفاده: /blocksticker نام_پک_استیکر")
        return

    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name not in blocked_packs:
        blocked_packs.append(pack_name)
        save_blocked(blocked_packs)
        await update.message.reply_text(f"✅ پک {pack_name} به لیست بلاک اضافه شد.", parse_mode="Markdown")
    else:
        await update.message.reply_text("این پک قبلاً توی لیست بلاک بوده.")

async def list_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, update.effective_user.id):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن این لیست رو ببینن.")
        return

    blocked_packs = load_blocked()
    if not blocked_packs:
        await update.message.reply_text("❌ هیچ پکی بلاک نشده.")
    else:
        text = "📛 پک‌های بلاک‌شده:\n" + "\n".join(f"• {p}" for p in blocked_packs)
        await update.message.reply_text(text, parse_mode="Markdown")

if name == "main":
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(CommandHandler("blocksticker", block_sticker))
    app.add_handler(CommandHandler("listblocked", list_blocked))

    app.run_polling()
