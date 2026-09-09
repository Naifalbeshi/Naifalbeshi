import os, threading
from flask import Flask
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

# كل رموز Exness بصيغة yfinance
SYMBOLS = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
    "XAUUSD": "GC=F", "XAGUSD": "SI=F", "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD", "US30": "^DJI", "NAS100": "^NDX", "SPX500": "^GSPC"
}

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Exness Scanner Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID: return
    await update.message.reply_text("سكانر Exness شغال ✅\nارسل /scan للفحص\nارسل /scan_all لفحص كل السوق")

async def scan_single(symbol_yf):
    try:
        data = yf.download(symbol_yf, period="1d", interval="15m", auto_adjust=True, progress=False)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.ta.rsi(length=14, append=True)
        data.ta.ema(length=50, append=True)
        last = data.iloc[-1]
        rsi = last['RSI_14']
        price = last['Close']
        ema = last['EMA_50']
        # منطق بسيط وواقعي
        if rsi < 30 and price > ema: return f"🟢 شراء قوي {symbol_yf} | RSI:{rsi:.1f}"
        if rsi > 70 and price < ema: return f"🔴 بيع قوي {symbol_yf} | RSI:{rsi:.1f}"
        return None
    except: return None

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID: return
    await update.message.reply_text("جاري فحص 10 رموز Exness...")
    results = []
    for name, yf_sym in SYMBOLS.items():
        sig = await scan_single(yf_sym)
        if sig: results.append(f"{name}: {sig}")
    if not results:
        await update.message.reply_text("لا يوجد فرص قوية الآن (RSI في المنتصف) - وهذا طبيعي في السكالبينج")
    else:
        await update.message.reply_text("\n".join(results))

def run_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("scan_all", scan))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
