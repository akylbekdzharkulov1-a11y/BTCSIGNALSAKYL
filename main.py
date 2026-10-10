from flask import Flask
import os, time, requests, threading
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route('/')
def home(): return "BTC Signals Akyl - SMC Free ✅"

def get_candles():
    try:
        # Binance Vision - 50 свеча 15м
        url = "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=50"
        data = requests.get(url, timeout=10).json()
        # [open time, open, high, low, close...]
        return [(float(c[2]), float(c[3]), float(c[4])) for c in data] # high, low, close
    except: return None

def bot_loop():
    print("✅ SMC BOT STARTED (Free TV logic)", flush=True)
    last_signal = ""
    while True:
        try:
            candles = get_candles()
            if not candles or len(candles) < 21:
                time.sleep(60); continue

            highs = [c[0] for c in candles]
            lows = [c[1] for c in candles]
            closes = [c[2] for c in candles]

            last_close = closes[-1]
            prev_high = max(highs[-21:-1])
            prev_low = min(lows[-21:-1])

            bishkek = datetime.now(timezone.utc) + timedelta(hours=6)
            t = bishkek.strftime("%H:%M")

            signal = None
            if last_close > prev_high:
                # BOS LONG
                entry = last_close
                sl = min(lows[-5:])
                tp1 = entry + (entry - sl)*1.5
                tp2 = entry + (entry - sl)*3
                signal = f"""🚀 SMC SIGNAL 🟢 LONG

💰 BTCUSDT: ${entry:,.2f}
📈 BOS Break! {prev_high:,.2f} сынды
📊 Себеп: Order Block + Liquidity Sweep
⏰ {t} Bishkek | 15m TF

🔹 Entry: ${entry:,.2f}
🔻 SL: ${sl:,.2f}
🎯 TP1: ${tp1:,.2f} (1.5R)
🎯 TP2: ${tp2:,.2f} (3R)

⚡️ Akyl Smart Money"""
            elif last_close < prev_low:
                entry = last_close
                sl = max(highs[-5:])
                tp1 = entry - (sl - entry)*1.5
                tp2 = entry - (sl - entry)*3
                signal = f"""🚀 SMC SIGNAL 🔴 SHORT

💰 BTCUSDT: ${entry:,.2f}
📉 BOS Break! {prev_low:,.2f} сынды
📊 Себеп: Liquidity Grab + CHoCH
⏰ {t} Bishkek | 15m TF

🔹 Entry: ${entry:,.2f}
🔻 SL: ${sl:,.2f}
🎯 TP1: ${tp1:,.2f} (1.5R)
🎯 TP2: ${tp2:,.2f} (3R)

⚡️ Akyl Smart Money"""

            # Сигнал кайталанбасын
            if signal and signal!= last_signal:
                r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                  data={"chat_id": CHAT_ID, "text": signal})
                print(f"📤 SMC {r.status_code} Price {last_close}", flush=True)
                last_signal = signal
            else:
                # жөнөкөй баа 15 мин сайын
                if int(time.time()) % 900 < 60:
                    txt = f"💰 BTC: ${last_close:,.2f} | Күтүүдө... BOS: Long>{prev_high:,.0f} Short<{prev_low:,.0f} ⏰{t}"
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                  data={"chat_id": CHAT_ID, "text": txt})

        except Exception as e:
            print(f"❌ {e}", flush=True)
        time.sleep(60) # ар 1 мин текшерет

threading.Thread(target=bot_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
