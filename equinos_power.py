import os
import json
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import gspread
from google.oauth2.service_account import Credentials

BOT_TOKEN = os.environ["8512404051:AAHfjDrMKwlfkrN9DSTFcXz_scsnNdRg8AQ"]
PUBLIC_URL = os.environ["https://app-gym-asistencias.onrender.com"].rstrip("/")
SHEET_ID = os.environ["1SeCGvCkq8xzkyA0ZKyMGSuwBIAvfN0fzeGZeVCrJE78"]
TAB_NAME = os.environ.get("TAB_NAME", "asistencias_gym")
GOOGLE_SA_JSON = os.environ["{
  "type": "service_account",
  "project_id": "mapsprokect",
  "private_key_id": "661c0b1257d677b36548f2b1fb49b7e4cc0fa71b",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCtOjJ53M6wP8O3\n2A/aK5d6kA/dVVDFwzQn0bJhTUP84gGtDOxSNHc9WICQlf5qYfMEo2c16hKMH7SE\nKOb9ipDsY9Vm0PGhXLlEaGPonwx11juMbRGJ3FYMSn2WylCvkSo9SeKsZnQ60qGB\nVcRVnT1Oso5nq0Ry2CeE9U6MxUUdaUYlrrDwpF+TvmnVSwzwUG/dqdQFnISUabXs\nQs55nmEVJr9PpJ87qt5jcx0C0cZ/junI/dMekxy78kcUEmjEfjOUJWVu38Fe0hyU\n93zywwzvAJg2qGrnpZb+FncakB6k0RbAPxB/DAP7r3TWvwYWOqotWXfh7fE7M0iy\nF/dxvDOhAgMBAAECggEAH/KbhA+V2/oKl9GkjM1c1MkUb/LP4IVBjXV2Y00bdJxf\nCEIZpIiSFDGKFoBfSVHyvqB/RLl8fbTMN1KO1WRUmZBI93siESs3bPces/R/WQ0v\nctTbtvP4t7AWTPTXoCWS53ZEtJx5o66chCyj9tE20RiLvHFhAJg+Y55VRA+O0V8/\nFyaifKYwNegGKOncL+oEV20eejq9Z0G4wWAv65jOrTNrtRr2+iZuXdLSDLTygRTn\nR9Ow+8+h0ZWZym0yWC7XX1h79QdhAid80a6Dj62a+IVi8fAWrjneNvEUADXVjgL0\nzMXma2HF/yh1ntXpX+UtPwc9dwZwJM/1N4iMz/JxxQKBgQDU4tKXxveBoFL9VseG\ngZ/mCpP2I9kg2CASAvBRAYxBtr+7FH0iEwviU4fKuTyfWFqeTgVMz1m/C1+oesfs\nRStt9OSk45y+3L5ZK1or8zxel8EQxG89iadqIRwNa0I38fQWoMkoZytHaJjE/K84\na0NuZgfHoIy0G5aUjE40CA0T/QKBgQDQT0Aut97H+XC/zXfIqu6yaDSgs2PM6qHz\ncOn1n6mSOT61DFuzobtBKve6/cNHa6vZeRNlUOEFQftfzd2mvRIAbiepvOgHhZaB\nC8opDbEvwoYQsp2koFVlikopsXfag0Kw0b2miNam8L+b8QKDflaD2GFLDPoLj8/q\ntpzhY2CldQKBgQCshAdu8dEfHcJDBLD6Qk9Gx2myPMi3Ag2zKuh+bMexdRwYyfjB\nxTeLOG/Bi60h4CLHSKio3xt2Ywwo5x7eTAtuttcW/FDIpvAmKKiRFzLj4QyWvuj6\nsHOX4K7v/OyTk6JfN/rrn/eFjbDHaZHBIcNqUoqZbnS3e+fiB3VUWvXmLQKBgQCO\nj+5pCsWZLomPetsjpng9+TsrUBpZP6sepIQ56c9vl2XnGlIYGfPBodpxSwK+el3e\nNBKmIDggFQwogQfU+Ui8qqbSb8qMe0yJfLwaZJiDCyode2CQLnrDR2WCK0bPcU3P\nHXwh4Tyme9VmsAb8XxZunUPYzUTDbOTqyZeMWSrnkQKBgC+kbVaiw5Z0hbOk/0et\nthbjPAr4+l8R/yjWb4OKX+U2a6dBRCtfrrbyMHuqvA9Rb10vYWUNsu9hS6YQHMxx\nHS4pjsG2x2bvdfE8vl7fhc97K0m42TcgHE9iWyCuRThKVE/mAA5Gt0Bn1outP54r\nSrdTAGeZaL4wJP2jY06Q9kI4\n-----END PRIVATE KEY-----\n",
  "client_email": "gym-app@mapsprokect.iam.gserviceaccount.com",
  "client_id": "105905620924255888824",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/gym-app%40mapsprokect.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}"]

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

    await update.message.reply_text("✅ Asistencia registrada. ¡Bien ahí! 💪")

tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("gym", gym))

@app.on_event("startup")
async def startup():
    await tg_app.bot.set_webhook(f"{PUBLIC_URL}/webhook")

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

@app.get("/")
def health():
    return {"status": "ok"}
