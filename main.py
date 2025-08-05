import random
import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    MessageEntity
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = "8381798336:AAFJzwST_zeCSEooXa2pL1YP8LF_MRZuGFg"
OWNER_ID = 1841766279  # ایدی عددی تو
GROUP_ID = -1001222208308  # گروه سگ مشکی
blocked_packs = []  # پک‌های بلاک شده
insults = ["خفه شو", "برو گمشو", "syfm", "الاغ", "چرت نگو", "sybau" , "بس" و "وخی"]  # می‌تونی بیشتر کنی


# --- دستورات مدیریتی ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات فعاله.")


async def block_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker:
        pack = update.message.sticker.set_name
        if pack not in blocked_packs:
            blocked_packs.append(pack)
            await update.message.reply_text(f"پک {pack} بلاک شد.")
        else:
            await update.message.reply_text("این پک قبلا بلاک شده.")


async def unblock_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        pack = context.args[0]
        if pack in blocked_packs:
            blocked_packs.remove(pack)
            await update.message.reply_text(f"پک {pack} آن‌بلاک شد.")
        else:
            await update.message.reply_text("این پک تو لیست بلاک نیست.")
    else:
        await update.message.reply_text("اسم پک رو بده.")


async def clear_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blocked_packs.clear()
    await update.message.reply_text("همه پک‌های بلاک پاک شدند.")


# --- مدیریت استیکر ---
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker = update.message.sticker
    user = update.message.from_user
    pack = sticker.set_name

    # بررسی ادمین بودن
    chat_admins = [admin.user.id async for admin in context.bot.get_chat_administrators(GROUP_ID)]
    if user.id in chat_admins:
        return

    if pack in blocked_packs:
        # حذف استیکر
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)

        # ساخت دکمه‌ها
        keyboard = [
            [
                InlineKeyboardButton("بیخیال", callback_data=f"ignore_{user.id}"),
                InlineKeyboardButton("فحش بده", callback_data=f"insult_{user.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # زمان
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # متن گزارش
        text = f"ادمین کاربر {user.full_name} در {now} استیکر زشت فرستاد."

        # ارسال گزارش به گروه
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=text,
            reply_markup=reply_markup
        )


# --- دکمه‌ها ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    chat_admins = [admin.user.id async for admin in context.bot.get_chat_administrators(GROUP_ID)]

    if data.startswith("ignore_"):
        if query.from_user.id in chat_admins:
            await query.edit_message_text("اوکی بیخیالش")
        else:
            await query.answer("فقط ادمین میتونه!", show_alert=True)

    elif data.startswith("insult_"):
        target_id = int(data.split("_")[1])
        if query.from_user.id in chat_admins:
            insult = random.choice(insults)
            await context.bot.send_message(
                GROUP_ID,
                f"[کاربر](tg://user?id={target_id}) {insult}",
                parse_mode="Markdown"
            )
        else:
            await query.answer("فقط ادمین میتونه!", show_alert=True)


# --- راه‌اندازی ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("blocksticker", block_sticker))
    app.add_handler(CommandHandler("unblocksticker", unblock_sticker))
    app.add_handler(CommandHandler("clearblocked", clear_blocked))
    app.add_handler(MessageHandler(filters.Sticker.ALL & filters.Chat(GROUP_ID), handle_sticker))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
