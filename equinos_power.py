import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import gspread
from google.oauth2.service_account import Credentials

# ===== ENV =====
BOT_TOKEN = os.environ["BOT_TOKEN"]
SHEET_ID = os.environ["SHEET_ID"]
TAB_NAME = os.environ.get("TAB_NAME", "asistencias")
PUBLIC_URL = os.environ["PUBLIC_URL"].rstrip("/")
GOOGLE_SA_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

TZ = ZoneInfo("America/Mexico_City")

app = FastAPI()

def get_sheet():
    info = json.loads(GOOGLE_SA_JSON)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet(TAB_NAME)
    return ws

# ===== Telegram app =====
tg_app = Application.builder().token(BOT_TOKEN).build()

async def gym(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    ts = now.isoformat()
    uid = str(user.id)

    ws = get_sheet()

    # Asumiendo columnas:
    # A: date | B: timestamp | C: user_id | D: username | E: nombre | F: chat_id | G: chat_title
    dates = ws.col_values(1)[1:]     # A sin header
    user_ids = ws.col_values(3)[1:]  # C sin header

    for d, u in zip(dates, user_ids):
        if d == today and u == uid:
            await update.message.reply_text("⚠️ Ya registraste tu asistencia hoy 💪")
            return

    row = [
        today,
        ts,
        uid,
        user.username or "",
        user.full_name or "",
        str(chat.id) if chat else "",
        chat.title if chat and chat.title else ""
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
    await update.message.reply_text("✅ Asistencia registrada. ¡Bien ahí! 💪")

tg_app.add_handler(CommandHandler("gym", gym))

@app.on_event("startup")
async def on_startup():
    webhook_url = f"{PUBLIC_URL}/webhook"
    # Se setea UNA VEZ al arrancar (no por comando)
    await tg_app.bot.delete_webhook(drop_pending_updates=True)
    await tg_app.bot.set_webhook(webhook_url)

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

@app.get("/")
def health():
    return {"status": "ok"}
