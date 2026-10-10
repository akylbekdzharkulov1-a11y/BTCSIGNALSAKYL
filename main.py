import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OFFSET = -96

@app.route('/')
def home(): return "BTC LIVE 15m"

def send(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=15)
        print(f"TG {r.status_code}", flush=True)
        return r.status_code == 200
    except Exception as e:
        print(f"TG ERR {e}", flush=True)
        return False

def get_price():
    try:
        j = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=30", timeout=10).json()
        highs = [float(x[2]) for x in j]
        lows = [float(x[3]) for x in j]
        closes = [float(x[4]) for x in j]
        binance = closes[-1]
        capital = binance + OFFSET
        return capital, binance, max(highs[-20:-1]), min(lows[-20:-1])
    except: return None

def loop():
    print("START 15M CAPITAL BOT", flush=True)
    send(f"✅ Бот кайра күйдү! {datetime.now().strftime('%H:%M')} - эми ар 15 мүнөттө Capital баасы келет")
    last = 0
    last_price = 0
    while True:
        try:
            data = get_price()
            if not data:
                time.sleep(20)
                continue
            cap, binp, prev_h, prev_l = data
            cap_h = prev_h + OFFSET
            cap_l = prev_l + OFFSET
            bish = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%H:%M")
            print(f"Capital ${cap:.2f}", flush=True)

            # BOS дароо
            if last_price!= 0:
                if cap > cap_h and last_price <= cap_h:
                    send(f"🚀 BOS LONG!\nCapital ${cap:,.2f} > R ${cap_h:,.0f}\nBinance ${binp:,.2f}\n{bish}")
                if cap < cap_l and last_price >= cap_l:
                    send(f"🚀 BOS SHORT!\nCapital ${cap:,.2f} < S ${cap_l:,.0f}\nBinance ${binp:,.2f}\n{bish}")

            # ар 15 мүнөттө отчет
            if time.time() - last > 900: # 900 = 15 минут
                send(f"""💎 BTC Capital {bish}
💰 Capital.com: ${cap:,.2f}
🏦 Binance: ${binp:,.2f} ({OFFSET}$)
🔴 R: ${cap_h+100:,.0f} / ${cap_h:,.0f}
🟢 S: ${cap_l:,.0f} / ${cap_l-100:,.0f}
BOS LONG >${cap_h:,.0f} | SHORT <${cap_l:,.0f}
⚡️ Akyl Capital 15m""")
                last = time.time()
            last_price = cap
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
        time.sleep(60)

threading.Thread(target=loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
