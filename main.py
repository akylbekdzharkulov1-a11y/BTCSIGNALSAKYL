from flask import Flask
import os, time, requests, threading, statistics
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route('/')
def home(): return "BTC PRO S/R VISION LIVE ✅"

def get_candles():
    urls = [
        "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=100",
        "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=100",
        "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=15&limit=100"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
            # Bybit өзгөчө
            if "bybit" in url:
                j = r.json()
                data = j['result']['list'][::-1]
                return [(float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in data]
            else:
                data = r.json()
                if isinstance(data, list) and len(data)>0 and isinstance(data[0], list):
                    # Binance: [time, open, high, low, close, vol]
                    return [(float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in data]
                else:
                    print(f"Bad data from {url}: {str(data)[:100]}", flush=True)
        except Exception as e:
            print(f"Fail {url[:25]} {e}", flush=True)
            continue
    return None

def bot_loop():
    print("✅ VISION BINANCE PRO STARTED", flush=True)
    last_hourly = 0
    last_signal = ""
    while True:
        try:
            candles = get_candles()
            if not candles:
                time.sleep(30); continue
            highs = [c[1] for c in candles]
            lows = [c[2] for c in candles]
            closes = [c[3] for c in candles]
            volumes = [c[4] for c in candles]
            last_close = closes[-1]
            avg_vol = statistics.mean(volumes[-21:-1])
            vol_ratio = volumes[-1]/avg_vol if avg_vol>0 else 1
            prev_high = max(highs[-21:-1])
            prev_low = min(lows[-21:-1])
            R1 = max(highs[-50:])
            S1 = min(lows[-50:])
            bishkek = datetime.now(timezone.utc) + timedelta(hours=6)
            t = bishkek.strftime("%H:%M")
            print(f"OK price=${last_close:.2f} H:{prev_high:.0f} L:{prev_low:.0f} Vol:{vol_ratio:.1f}x", flush=True)

            if time.time() - last_hourly > 3600:
                txt = f"""💎 BTC PRO S/R | {t} | Vision

💰 БАА: ${last_close:,.2f}
🏦 Bybit/Binance: ${last_close:,.2f} | {vol_ratio:.1f}x

🔴 RESISTANCE: ${R1:,.0f} (BOS LONG >${prev_high:,.0f})
🟢 SUPPORT: ${S1:,.0f} (BOS SHORT <${prev_low:,.0f})

Тренд линия: ${S1:,.0f} -> ${R1:,.0f}
Кит: {vol_ratio:.1f}x

⚡️ Akyl Pro"""
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": txt})
                last_hourly = time.time()
        except Exception as e:
            print(f"Loop {e}", flush=True)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
