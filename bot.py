import os
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = os.environ["TOKEN"]

# In-memory storage
waiting_users = {"male": [], "female": []}
active_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Anonymous Chat!\n"
        "Use /male or /female to set your gender.\n"
        "Then use /match to find a chat partner.\n"
        "Use /stop to end the chat."
    )

async def set_male(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = "male"
    await update.message.reply_text("✅ Gender set to male.")

async def set_female(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = "female"
    await update.message.reply_text("✅ Gender set to female.")

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    gender = context.user_data.get("gender")

    if gender not in ["male", "female"]:
        await update.message.reply_text("⚠️ Please set your gender using /male or /female.")
        return

    opposite = "female" if gender == "male" else "male"

    if waiting_users[opposite]:
        partner_id = waiting_users[opposite].pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await context.bot.send_message(chat_id=user_id, text="🎉 Partner found! Say hi!")
        await context.bot.send_message(chat_id=partner_id, text="🎉 Partner found! Say hi!")
    else:
        if user_id not in waiting_users[gender]:
            waiting_users[gender].append(user_id)
            await update.message.reply_text("⏳ Waiting for a partner...")
        else:
            await update.message.reply_text("⏳ Still waiting for a match...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = active_chats.pop(user_id, None)

    if partner_id:
        active_chats.pop(partner_id, None)
        await context.bot.send_message(chat_id=partner_id, text="🚫 Your partner left the chat.")
        await update.message.reply_text("✅ You have left the chat.")
    else:
        await update.message.reply_text("❌ You're not in a chat.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = active_chats.get(user_id)

    if partner_id:
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("💬 You're not in a chat. Use /match to find a partner.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("male", set_male))
    app.add_handler(CommandHandler("female", set_female))
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
