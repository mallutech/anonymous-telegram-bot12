import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Get bot token from environment
TOKEN = os.environ.get("TOKEN")

# In-memory user queues and chat pairs
male_queue = []
female_queue = []
chat_pairs = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Anonymous Chat Bot!\n"
        "Use /male or /female to find a chat partner.\n"
        "Use /leave to exit the chat anytime."
    )

# /male command
async def male(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in chat_pairs:
        await update.message.reply_text("❗ You're already in a chat. Type /leave to exit.")
        return

    if female_queue:
        partner_id = female_queue.pop(0)
        chat_pairs[user_id] = partner_id
        chat_pairs[partner_id] = user_id

        await context.bot.send_message(partner_id, "🔗 Connected to a male partner. Start chatting!")
        await update.message.reply_text("🔗 Connected to a female partner. Start chatting!")
    else:
        male_queue.append(user_id)
        await update.message.reply_text("⏳ Waiting for a female partner...")

# /female command
async def female(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in chat_pairs:
        await update.message.reply_text("❗ You're already in a chat. Type /leave to exit.")
        return

    if male_queue:
        partner_id = male_queue.pop(0)
        chat_pairs[user_id] = partner_id
        chat_pairs[partner_id] = user_id

        await context.bot.send_message(partner_id, "🔗 Connected to a female partner. Start chatting!")
        await update.message.reply_text("🔗 Connected to a male partner. Start chatting!")
    else:
        female_queue.append(user_id)
        await update.message.reply_text("⏳ Waiting for a male partner...")

# /leave command
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in chat_pairs:
        partner_id = chat_pairs.pop(user_id)
        chat_pairs.pop(partner_id, None)

        await context.bot.send_message(partner_id, "❌ Your partner left the chat.")
        await update.message.reply_text("❌ You left the chat.")
    else:
        if user_id in male_queue:
            male_queue.remove(user_id)
        if user_id in female_queue:
            female_queue.remove(user_id)
        await update.message.reply_text("❌ You're not in a chat.")

# Handle messages and media
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in chat_pairs:
        partner_id = chat_pairs[user_id]
        if update.message.text:
            await context.bot.send_message(partner_id, text=update.message.text)
        elif update.message.sticker:
            await context.bot.send_sticker(partner_id, sticker=update.message.sticker.file_id)
        elif update.message.photo:
            await context.bot.send_photo(partner_id, photo=update.message.photo[-1].file_id)
        elif update.message.video:
            await context.bot.send_video(partner_id, video=update.message.video.file_id)
    else:
        await update.message.reply_text("❗ You're not in a chat. Use /male or /female to find a partner.")

# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("male", male))
    app.add_handler(CommandHandler("female", female))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
