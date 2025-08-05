import logging
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Store user data
users = {}
waiting_male = []
waiting_female = []
active_chats = {}

# Gender selection keyboard
gender_keyboard = ReplyKeyboardMarkup(
    [["Male", "Female"]], one_time_keyboard=True, resize_keyboard=True
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = {"gender": None, "partner": None}
    await update.message.reply_text("Welcome to Anonymous Chat!\nPlease select your gender:", reply_markup=gender_keyboard)

# Handle gender
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if text not in ["male", "female"]:
        await update.message.reply_text("Please select a valid gender (Male/Female).")
        return

    users[user_id]["gender"] = text
    await update.message.reply_text("Looking for a match...")

    await match_users(user_id)

# Match logic
async def match_users(user_id):
    user_gender = users[user_id]["gender"]
    opposite_queue = waiting_female if user_gender == "male" else waiting_male
    own_queue = waiting_male if user_gender == "male" else waiting_female

    if opposite_queue:
        partner_id = opposite_queue.pop(0)
        users[user_id]["partner"] = partner_id
        users[partner_id]["partner"] = user_id

        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await send_message(user_id, "✅ Matched! Say hi anonymously.")
        await send_message(partner_id, "✅ Matched! Say hi anonymously.")
    else:
        own_queue.append(user_id)
        await send_message(user_id, "Waiting for a partner...")

# Handle chat messages
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = users.get(user_id, {}).get("partner")

    if partner_id:
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("❗You're not matched yet. Please wait or /start again.")

# End chat
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = users.get(user_id, {}).get("partner")

    if partner_id:
        await send_message(partner_id, "🚫 Your partner has left the chat.")
        users[partner_id]["partner"] = None
        active_chats.pop(partner_id, None)

    users[user_id]["partner"] = None
    active_chats.pop(user_id, None)

    await update.message.reply_text("❌ You left the chat. Use /start to begin again.")

# Utility send
async def send_message(user_id, text):
    try:
        await app.bot.send_message(chat_id=user_id, text=text)
    except Exception as e:
        logger.warning(f"Failed to send message to {user_id}: {e}")

# Main setup
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.Regex("^(Male|Female)$"), gender))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), forward_message))

    print("Bot is running...")
    app.run_polling()
    
