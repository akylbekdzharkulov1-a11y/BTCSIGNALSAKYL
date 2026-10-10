from flask import Flask
import os, time, requests, threading
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route('/')
def home(): return "BTC Signals Akyl - SMC FIX ✅"

def get_candles():
    # 1. Bybit - Render'де эң жакшы иштейт
    try:
        url = "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=15&limit=50"
        r = requests.get(url, timeout=10).json()
        data = r['result']['list'][::-1] # тескери
        # [start, open, high, low, close]
        return [(float(c[2]), float(c[3]), float(c[4])) for c in data]
    except Exception as e:
        print(f"Bybit fail {e}", flush=True)
    # 2. OKX
    try:
        url = "https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=15m&limit=50"
        r = requests.get(url, timeout=10).json()
        data = r['data'][::-1]
        return [(float(c[2]), float(c[3]), float(c[4])) for c in data]
    except Exception as e:
        print(f"OKX fail {e}", flush=True)
    # 3. Binance vision
    try:
        url = "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=50"
        data = requests.get(url, timeout=10).json()
        return [(float(c[2]), float(c[3]), float(c[4])) for c in data]
    except Exception as e:
        print(f"Binance fail {e}", flush=True)
    return None

def get_price():
    try:
        r = requests.get("https://api.bybit.com/v5/market/tickers?category=spot&symbol=BTCUSDT", timeout=5).json()
        return float(r['result']['list'][0]['lastPrice'])
    except:
        try:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()
            return float(r['bitcoin']['usd'])
        except: return None

def bot_loop():
    print("✅ SMC BOT STARTED FIX v2", flush=True)
    last_signal = ""
    while True:
        try:
            p = get_price()
            candles = get_candles()
            print(f"DEBUG price={p} candles={len(candles) if candles else 0}", flush=True)

            if not p or not candles or len(candles) < 21:
                time.sleep(30); continue

            highs = [c[0] for c in candles]
            lows = [c[1] for c in candles]
            closes = [c[2] for c in candles]
            last_close = closes[-1]
            prev_high = max(highs[-21:-1])
            prev_low = min(lows[-21:-1])

            bishkek = datetime.now(timezone.utc) + timedelta(hours=6)
            t = bishkek.strftime("%H:%M")

            # Ар 15 мүнөттө жөнөкөй баа + BOS денгээлдери
            txt = f"💰 BTC: ${last_close:,.2f} (${p:,.2f})\n📊 BOS: LONG>{prev_high:,.0f} | SHORT<{prev_low:,.0f}\n⏰ {t} Bishkek | SMC күтүүдө..."
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": txt}, timeout=10)
            print(f"📤 Sent BTC {last_close} BOS H:{prev_high} L:{prev_low}", flush=True)

        except Exception as e:
            print(f"❌ LOOP {e}", flush=True)
        time.sleep(300) # 5 мүнөт

threading.Thread(target=bot_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
