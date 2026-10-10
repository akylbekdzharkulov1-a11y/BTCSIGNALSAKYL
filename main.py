from flask import Flask
import os, time, requests, threading, statistics
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# УШУЛ ЖЕРДИ CAPITAL.COM ГА ШАЙКЕШ КЫЛАБЫЗ
CAPITAL_OFFSET = -96 # Capital.com Binance'тен ~96$ арзан, ошондуктан -96

@app.route('/')
def home(): return "BTC CAPITAL MATCHED ✅"

def get_candles():
    urls = [
        "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=100",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
            data = r.json()
            if isinstance(data, list) and len(data)>0:
                return [(float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in data]
        except: continue
    return None

def bot_loop():
    print(f"✅ CAPITAL OFFSET {CAPITAL_OFFSET} MODE", flush=True)
    last_hourly = 0
    while True:
        try:
            candles = get_candles()
            if not candles: time.sleep(30); continue

            highs = [c[1]+CAPITAL_OFFSET for c in candles]
            lows = [c[2]+CAPITAL_OFFSET for c in candles]
            closes = [c[3]+CAPITAL_OFFSET for c in candles]
            volumes = [c[4] for c in candles]

            last_close = closes[-1]
            avg_vol = statistics.mean(volumes[-21:-1])
            vol_ratio = volumes[-1]/avg_vol if avg_vol>0 else 1
            prev_high = max(highs[-21:-1])
            prev_low = min(lows[-21:-1])

            bishkek = datetime.now(timezone.utc) + timedelta(hours=6)
            t = bishkek.strftime("%H:%M")

            print(f"OK Capital Price=${last_close:.2f} (Binance {last_close-CAPITAL_OFFSET:.2f} {CAPITAL_OFFSET})", flush=True)

            if time.time() - last_hourly > 3600:
                txt = f"""💎 BTC | Capital.com шайкеш | {t}

💰 Capital.com БАА: ${last_close:,.2f}
🏦 Binance Spot: ${last_close-CAPITAL_OFFSET:,.2f} (Айырма {CAPITAL_OFFSET}$)
📊 TradingView (Capital.com): Сенин чарт менен дал келет!

🔴 RESISTANCE: ${prev_high+150:,.0f} / ${prev_high:,.0f}
🟢 SUPPORT: ${prev_low:,.0f} / ${prev_low-150:,.0f}

Тренд линия: ${prev_low:,.0f} -> ${prev_high:,.0f}
Кит: {vol_ratio:.1f}x

⚡️ Akyl Capital Matched"""
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": txt})
                last_hourly = time.time()
        except Exception as e:
            print(f"ERR {e}", flush=True)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
