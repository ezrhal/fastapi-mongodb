from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot 😊")

async def medaltally(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏅 Here’s the medal tally!")

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [{"text": "🏀 Basketball", "callback_data": "basketball"}],
        [{"text": "⚾ Baseball", "callback_data": "baseball"}],
    ]
    await update.message.reply_text(
        "Choose a sport:",
        reply_markup={"inline_keyboard": keyboard}
    )


start_handler = CommandHandler("start", start)
medaltally_handler = CommandHandler("medaltally", medaltally)