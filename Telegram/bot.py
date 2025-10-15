from fastapi import FastAPI, Request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler
from fastapi import APIRouter

import asyncio
import os

BOT_TOKEN = "7554480933:AAESR3boR9NapytAl_dNkiMrYIXrh2doUm4"

router = APIRouter()

telegram_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context):
    keyboard = [
        [KeyboardButton("🗓 Schedule")],
        [KeyboardButton("🎛 Buttons Editor"), KeyboardButton("📝 Posts Editor")],
        [KeyboardButton("💵 Balance"), KeyboardButton("🔐 Admin")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

# Add /start command handler
telegram_app.add_handler(CommandHandler("start", start))

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram"""
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}