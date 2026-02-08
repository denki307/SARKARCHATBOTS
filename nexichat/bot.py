import os
import re
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatPermissions
from replies import get_reply, BAD_WORDS

TOKEN = os.getenv("BOT_TOKEN")

WARN_LIMIT = 3
WARN_DATA = {}
LAST_MESSAGES = {}

def is_admin(update, context):
    member = context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return member.status in ["administrator", "creator"]

def contains_link(text):
    link_pattern = r"(http://|https://|www\.|t\.me/)"
    return re.search(link_pattern, text) is not None

def start(update, context):
    update.message.reply_text(
        "🤖 Tamil Group Moderation Bot\n\n"
        "Admin Commands:\n"
        "/warn (reply)\n"
        "/unmute (reply)\n"
        "/kick (reply)"
    )

def warn(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ Admin only")
        return

    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to user")
        return

    user = update.message.reply_to_message.from_user
    uid = user.id

    WARN_DATA[uid] = WARN_DATA.get(uid, 0) + 1

    if WARN_DATA[uid] >= WARN_LIMIT:
        until = datetime.now() + timedelta(minutes=10)
        context.bot.restrict_chat_member(
            update.effective_chat.id,
            uid,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        WARN_DATA[uid] = 0
        update.message.reply_text(f"🔇 {user.first_name} muted (3 warns)")
    else:
        update.message.reply_text(
            f"⚠️ Warn {WARN_DATA[uid]}/{WARN_LIMIT} – {user.first_name}"
        )

def unmute(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ Admin only")
        return

    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to user")
        return

    uid = update.message.reply_to_message.from_user.id
    context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    update.message.reply_text("🔊 User unmuted")

def kick(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ Admin only")
        return

    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to user")
        return

    uid = update.message.reply_to_message.from_user.id
    context.bot.kick_chat_member(update.effective_chat.id, uid)
    update.message.reply_text("👢 User kicked")

def auto_moderate(update, context):
    msg = update.message
    uid = msg.from_user.id
    text = msg.text.lower()

    if contains_link(text):
        msg.delete()
        return

    for w in BAD_WORDS:
        if w in text:
            msg.delete()
            return

    if uid in LAST_MESSAGES and LAST_MESSAGES[uid] == text:
        msg.delete()
        return

    LAST_MESSAGES[uid] = text
    msg.reply_text(get_reply())

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("unmute", unmute))
    dp.add_handler(CommandHandler("kick", kick))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_moderate))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
