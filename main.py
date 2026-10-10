import os, time, requests, threading
from flask import Flask
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OFFSET = -96

@app.route('/')
def home(): return "BTC BOS ONLY ✅"

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=10)
        print(f"TG SENT BOS", flush=True)
    except: pass

def get_data():
    try:
        j = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=50", timeout=10).json()
        closes = [float(x[4])+OFFSET for x in j]
        highs = [float(x[2])+OFFSET for x in j]
        lows = [float(x[3])+OFFSET for x in j]
        return closes[-1], max(highs[-21:-1]), min(lows[-21:-1])
    except: return None

def loop():
    print("BOS ONLY MODE STARTED", flush=True)
    send(f"✅ BOS ONLY күйдү! Эми 15 мүнөттүк спам жок, BOS болсо гана келет. {datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=6))).strftime('%H:%M')}")
    last_price = 0
    while True:
        try:
            data = get_data()
            if not data: time.sleep(20); continue
            cap, cap_h, cap_l = data
            print(f"Check Capital ${cap:.2f} R{cap_h:.0f} S{cap_l:.0f}", flush=True)
            bish = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%H:%M")

            if last_price!= 0:
                if cap > cap_h and last_price <= cap_h:
                    send(f"""🚀 BOS LONG! BREAKOUT!

💰 Capital: ${cap:,.2f}
🔴 Сынды: ${cap_h:,.0f}
🕐 {bish} Бишкек

✅ СЕТАП:
LONG ач -> SL ${cap_l-100:,.0f} / TP +$150 +$300""")
                if cap < cap_l and last_price >= cap_l:
                    send(f"""🚀 BOS SHORT! BREAKDOWN!

💰 Capital: ${cap:,.2f}
🟢 Сынды: ${cap_l:,.0f}
🕐 {bish} Бишкек

✅ СЕТАП:
SHORT ач -> SL ${cap_h+100:,.0f} / TP -$150 -$300""")
            last_price = cap
        except Exception as e:
            print(f"ERR {e}", flush=True)
        time.sleep(60)

threading.Thread(target=loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
