import os
import threading
from flask import Flask
import yfinance as yf
import pandas_ta as ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

# هذا سيرفر وهمي عشان Render يشوف انك شغال
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("البوت شغال ✅\nارسل /scan")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("جاري الفحص...")
    try:
        data = yf.download("BTC-USD", period="1d", interval="15m")
        data.ta.rsi(length=14, append=True)
        last_rsi = data['RSI_14'].iloc[-1]
        price = data['Close'].iloc[-1]
        msg = f"BTC: {price:.2f}\nRSI: {last_rsi:.2f}"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

def run_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
