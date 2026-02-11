import os
import json
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import gspread
from google.oauth2.service_account import Credentials

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
PUBLIC_URL = os.environ["PUBLIC_URL"].rstrip("/")
SHEET_ID = os.environ["SHEET_ID"]
TAB_NAME = os.environ.get("TAB_NAME", "asistencias")
GOOGLE_SA_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

app = FastAPI()


def get_ws():
    info = json.loads(GOOGLE_SA_JSON)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    return sh.worksheet(TAB_NAME)


async def gym(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    ts = datetime.now(timezone.utc).isoformat()

    row = [
        ts,
        str(user.id),
        user.username or "",
        user.full_name or "",
        str(chat.id) if chat else "",
        (chat.title if chat and chat.title else "") if chat else ""
    ]

    ws = get_ws()
    ws.append_row(row, value_input_option="USER_ENTERED")

    # En algunos casos (mensajes de canal, etc.) update.message puede venir None
    if update.message:
        await update.message.reply_text("✅ Asistencia registrada. ¡Bien ahí! 💪")


tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("gym", gym))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot vivo. Prueba /gym")

tg_app.add_handler(CommandHandler("start", start))


@app.on_event("startup")
async def startup():
    # ✅ Inicializa y arranca PTB antes de procesar updates (evita RuntimeError)
    await tg_app.initialize()
    await tg_app.start()

    # ✅ Configura el webhook apuntando a tu Render URL
    await tg_app.bot.set_webhook(f"{PUBLIC_URL}/webhook")


@app.on_event("shutdown")
async def shutdown():
    # ✅ Apagado limpio
    await tg_app.stop()
    await tg_app.shutdown()


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


@app.get("/")
def health():
    return {"status": "ok"}
    
@app.get("/debug/sheets")
def debug_sheets():
    ws = get_ws()
    ws.append_row(["debug", "ok"], value_input_option="USER_ENTERED")
    return {"ok": True}
    
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    # 👇 Esto te dice si Telegram está mandando mensajes
    msg = data.get("message") or data.get("edited_message") or {}
    text = msg.get("text")
    chat = msg.get("chat", {})
    print("INCOMING:", {"text": text, "chat_id": chat.get("id"), "chat_type": chat.get("type")})

    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


    




