
import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

waiting_users = {"male": [], "female": []}
active_chats = {}

gender_keyboard = ReplyKeyboardMarkup([["Male", "Female"]], one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Anonymous Chat! Please select your gender:",
        reply_markup=gender_keyboard
    )

async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.lower()
    user_id = update.message.from_user.id

    if gender not in ["male", "female"]:
        await update.message.reply_text("Please choose Male or Female.")
        return

    opposite = "female" if gender == "male" else "male"
    
    if waiting_users[opposite]:
        partner_id = waiting_users[opposite].pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await context.bot.send_message(partner_id, "🎉 You are now connected to a stranger. Say hi!")
        await update.message.reply_text("🎉 You are now connected to a stranger. Say hi!")
    else:
        waiting_users[gender].append(user_id)
        await update.message.reply_text("⏳ Waiting for someone to connect...")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.message.from_user.id
    if sender_id in active_chats:
        partner_id = active_chats[sender_id]
        await context.bot.send_message(partner_id, update.message.text)
    else:
        await update.message.reply_text("❗ You're not connected to anyone. Use /start to find a partner.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)

        await context.bot.send_message(partner_id, "🚫 The other person has left the chat.")
        await update.message.reply_text("🚫 You have left the chat.")
    else:
        await update.message.reply_text("You're not in a chat right now.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gender))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot is running...")
    app.run_polling()
