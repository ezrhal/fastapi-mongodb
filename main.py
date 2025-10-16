from contextlib import asynccontextmanager
from unicodedata import lookup

from fastapi import FastAPI, Request
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware
from telegram import Update

from config.db.pmis_db import engine
from routes import doc_route, reference, verify_user, refresh, calendar
from routes.DTS import document, recipient, upload, lookup
from routes.Reference import pmis_office
from routes.route import router
from Telegram import bot
from config.minio_config import minio_client, S3_DTS_BUCKET

from fastapi import FastAPI

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi import FastAPI
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from Telegram.bot import start_handler, medaltally_handler

# async def ensure_bucket():
#     found = minio_client.bucket_exists(S3_DTS_BUCKET)
#     if not found:
#         minio_client.make_bucket(S3_DTS_BUCKET)
BOT_TOKEN = "7554480933:AAESR3boR9NapytAl_dNkiMrYIXrh2doUm4"
webhook_url = "https://workflow.pgas.ph:88/webhook"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=webhook_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        # await ensure_bucket()
    yield

app = FastAPI(lifespan=lifespan)

telegram_app = Application.builder().token(BOT_TOKEN).build()
telegram_app.add_handler(start_handler)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


origins = [
    "http://localhost:5173",  # Example: Allow a frontend running on localhost:3000
    "https://pgas.ph",  # Example: Allow a specific production domain
    "http://localhost"
]

# Add CORSMiddleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods (e.g., GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers
)





#
# @app.on_event("startup")
# async def on_startup():
#     # Create tables
#     async with engine.begin() as conn:
#         await conn.run_sync(SQLModel.metadata.create_all)

app.include_router(doc_route.router, prefix="/docs", tags=["docs"])
app.include_router(reference.router, prefix="/refs", tags=["refs"])
app.include_router(verify_user.router, prefix="/auth", tags=["auth"])
app.include_router(refresh.router, prefix="/authorize", tags=["authorize"])
app.include_router(calendar.router, prefix="/test", tags=["test"])

## region DTS
app.include_router(document.router, prefix="/document", tags=["document"])
app.include_router(recipient.router, prefix="/document/recipient", tags=["document"])
app.include_router(upload.router, prefix="/document/upload", tags=["document"])

## endregion

## region REFERENCE
app.include_router(lookup.router, prefix="/reference", tags=["reference"])
app.include_router(pmis_office.router, prefix="/reference", tags=["offices"])

## endregion

app.include_router(router)