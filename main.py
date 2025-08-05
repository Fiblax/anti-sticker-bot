import os
import json
import random
from datetime import datetime
from telegram import (
    Update, ChatMember, InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand
)
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# تنظیمات اصلی
TOKEN = "8381798336:AAFJzwST_zeCSEooXa2pL1YP8LF_MRZuGFg"
GROUP_ID = -1001222208308
OWNER_ID = 1841766279
BLOCKED_FILE = "blocked.json"

# فحش‌ها (می‌توانی بعداً تغییرشان بدهی)
INSULTS = [
    "احمق", "کله‌پو", "بی‌مغز", "خر", "سگ کثیف", "عوضی", "گاو", "مغز فندوقی",
    "نخودی", "پفیوز", "خنگول", "بیشعور", "دیلاق", "کله‌پوک", "چرت‌خور", "هالو",
    "کچل"، "ننه‌خر", "بزغاله", "انگشت‌چشم"
]

# ---- مدیریت فایل بلاک ----
def load_blocked():
    if not os.path.exists(BLOCKED_FILE):
        return []
    with open(BLOCKED_FILE, "r") as f:
        return json.load(f)

def save_blocked(blocked_packs):
    with open(BLOCKED_FILE, "w") as f:
        json.dump(blocked_packs, f)

# ---- بررسی ادمین ----
async def is_user_admin(update: Update, user_id: int):
    member = await update.effective_chat.get_member(user_id)
    return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]

# ---- هندل استیکر ----
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    sticker = update.message.sticker
    blocked_packs = load_blocked()

    if sticker.set_name and sticker.set_name in blocked_packs:
        await update.message.delete()

        # گزارش به گروه
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("بیخیال", callback_data=f"ignore_{update.message.from_user.id}"),
                InlineKeyboardButton("فحش بده", callback_data=f"insult_{update.message.from_user.id}")
            ]
        ])
        text = (
            f"[مالک](tg://user?id={OWNER_ID})\n"
            f"یک استیکر بلاک‌شده حذف شد.\n"
            f"از طرف: [{update.message.from_user.first_name}](tg://user?id={update.message.from_user.id})\n"
            f"تاریخ و ساعت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

# ---- بلاک کردن پک ----
async def block_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن این دستور رو استفاده کنن.")

    if not context.args:
        return await update.message.reply_text("استفاده: /blocksticker نام_پک_استیکر")

    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name not in blocked_packs:
        blocked_packs.append(pack_name)
        save_blocked(blocked_packs)
        await update.message.reply_text(f"✅ پک {pack_name} بلاک شد.")
    else:
        await update.message.reply_text("این پک قبلاً بلاک شده.")

# ---- آن‌بلاک کردن پک ----
async def unblock_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن این دستور رو استفاده کنن.")

    if not context.args:
        return await update.message.reply_text("استفاده: /unblocksticker نام_پک_استیکر")

    pack_name = context.args[0]
    blocked_packs = load_blocked()
    if pack_name in blocked_packs:
        blocked_packs.remove(pack_name)
        save_blocked(blocked_packs)
        await update.message.reply_text(f"♻️ پک {pack_name} آن‌بلاک شد.")
    else:
        await update.message.reply_text("این پک توی لیست بلاک نیست.")

# ---- لیست پک‌های بلاک ----
async def list_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن این دستور رو استفاده کنن.")

    blocked_packs = load_blocked()
    if not blocked_packs:
        await update.message.reply_text("❌ هیچ پکی بلاک نشده.")
    else:
        text = "📛 پک‌های بلاک‌شده:\n" + "\n".join(f"• {p}" for p in blocked_packs)
        await update.message.reply_text(text)

# ---- پاک کردن کل لیست بلاک ----
async def clear_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not await is_user_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔️ فقط ادمین‌ها می‌تونن این دستور رو استفاده کنن.")

    save_blocked([])
    await update.message.reply_text("🗑 لیست پک‌های بلاک پاک شد.")

# ---- هندل دکمه‌ها ----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_user_admin(update, query.from_user.id):
        return await query.answer("فقط ادمین‌ها می‌تونن از این دکمه‌ها استفاده کنن.", show_alert=True)

    data = query.data
    if data.startswith("ignore_"):
        await query.edit_message_text("اوکی بیخیالش")
    elif data.startswith("insult_"):
        target_id = data.split("_")[1]
        insult = random.choice(INSULTS)
        await query.edit_message_text(f"[کاربر](tg://user?id={target_id}) {insult}", parse_mode="Markdown")

# ---- تنظیم دستورات در منوی / ----
async def set_commands(app):
    commands = [
        BotCommand("blocksticker", "بلاک کردن پک استیکر"),
        BotCommand("unblocksticker", "آنبلاک کردن پک استیکر"),
        BotCommand("listblocked", "نمایش لیست پک‌های بلاک‌شده"),
        BotCommand("clearblocked", "پاک کردن همه پک‌های بلاک")
    ]
    await app.bot.set_my_commands(commands)

# ---- اجرای ربات ----
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(CommandHandler("blocksticker", block_sticker))
    app.add_handler(CommandHandler("unblocksticker", unblock_sticker))
    app.add_handler(CommandHandler("listblocked", list_blocked))
    app.add_handler(CommandHandler("clearblocked", clear_blocked))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.post_init = lambda _: set_commands(app)
    app.run_polling()
