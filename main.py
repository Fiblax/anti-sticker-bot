from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, MessageEntity
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext
import random
import datetime

TOKEN = "8381798336:AAFJzwST_zeCSEooXa2pL1YP8LF_MRZuGFg"
OWNER_ID = 1841766279  # ایدی عددی تو
GROUP_ID = -1001222208308  # گروه سگ مشکی
blocked_packs = []  # پک‌های بلاک شده
insults = ["خفه شو", "برو گمشو", "گاو", "الاغ", "چرت نگو", "عوضی"]  # می‌تونی بیشتر کنی

def start(update: Update, context: CallbackContext):
    update.message.reply_text("ربات فعاله.")

def block_sticker(update: Update, context: CallbackContext):
    if update.message.sticker:
        pack = update.message.sticker.set_name
        if pack not in blocked_packs:
            blocked_packs.append(pack)
            update.message.reply_text(f"پک {pack} بلاک شد.")
        else:
            update.message.reply_text("این پک قبلا بلاک شده.")

def unblock_sticker(update: Update, context: CallbackContext):
    if context.args:
        pack = context.args[0]
        if pack in blocked_packs:
            blocked_packs.remove(pack)
            update.message.reply_text(f"پک {pack} آن‌بلاک شد.")
        else:
            update.message.reply_text("این پک تو لیست بلاک نیست.")
    else:
        update.message.reply_text("اسم پک رو بده.")

def clear_blocked(update: Update, context: CallbackContext):
    blocked_packs.clear()
    update.message.reply_text("همه پک‌های بلاک پاک شدند.")

def handle_sticker(update: Update, context: CallbackContext):
    sticker = update.message.sticker
    user = update.message.from_user
    pack = sticker.set_name

    # ادمین‌ها معافند
    chat_admins = [admin.user.id for admin in context.bot.get_chat_administrators(GROUP_ID)]
    if user.id in chat_admins:
        return

    if pack in blocked_packs:
        # حذف استیکر
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)

        # ساخت دکمه‌ها
        keyboard = [
            [
                InlineKeyboardButton("بیخیال", callback_data=f"ignore_{user.id}"),
                InlineKeyboardButton("فحش بده", callback_data=f"insult_{user.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # ساخت پیام گزارش
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ایجاد entities برای تگ کردن
        entities = []

        text = f"ادمین کاربر  در {now} استیکر زشت فرستاد."
        # تگ ادمین
        entities.append(MessageEntity(type="text_mention", offset=0, length=5, user=context.bot.get_chat_member(GROUP_ID, OWNER_ID).user))
        # لینک به کاربر
        user_display_name = user.full_name
        user_offset = text.index("کاربر")
        entities.append(MessageEntity(type="text_mention", offset=user_offset + 6, length=len(user_display_name), user=user))

        # ارسال گزارش
        context.bot.send_message(
            chat_id=GROUP_ID,
            text=text.replace("کاربر ", f"کاربر {user_display_name}"),
            reply_to_message_id=update.message.message_id,
            reply_markup=reply_markup,
            entities=entities
        )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_admins = [admin.user.id for admin in context.bot.get_chat_administrators(GROUP_ID)]

    if data.startswith("ignore_"):
        if query.from_user.id in chat_admins:
            query.edit_message_text("اوکی بیخیالش")
        else:
            query.answer("فقط ادمین میتونه!", show_alert=True)

    elif data.startswith("insult_"):
        target_id = int(data.split("_")[1])
        if query.from_user.id in chat_admins:
            insult = random.choice(insults)
            context.bot.send_message(GROUP_ID, f"[کاربر](tg://user?id={target_id}) {insult}", parse_mode="Markdown")
        else:
            query.answer("فقط ادمین میتونه!", show_alert=True)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("blocksticker", block_sticker))
    dp.add_handler(CommandHandler("unblocksticker", unblock_sticker))
    dp.add_handler(CommandHandler("clearblocked", clear_blocked))
    dp.add_handler(MessageHandler(Filters.sticker & Filters.chat(GROUP_ID), handle_sticker))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
