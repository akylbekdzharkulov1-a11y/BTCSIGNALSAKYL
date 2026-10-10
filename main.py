from flask import Flask
import os, time, requests, threading, statistics
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route('/')
def home(): return "BTC PRO S/R LIVE ✅"

def get_candles():
    for _ in range(3):
        try:
            url = "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=15&limit=100"
            r = requests.get(url, timeout=15)
            j = r.json()
            if 'result' in j and 'list' in j['result']:
                data = j['result']['list'][::-1]
                return [(float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in data]
        except: time.sleep(2)
    return None

def bot_loop():
    print("✅ PRO S/R MODE STARTED", flush=True)
    last_signal = ""
    last_hourly = 0
    while True:
        try:
            candles = get_candles()
            if not candles or len(candles)<40:
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

            # S/R 3 деңгээл
            all_highs = sorted(set([round(h) for h in highs[-50:]]), reverse=True)
            all_lows = sorted(set([round(l) for l in lows[-50:]]))
            R1 = all_highs[0] if len(all_highs)>0 else prev_high
            R2 = all_highs[1] if len(all_highs)>1 else R1+300
            R3 = all_highs[2] if len(all_highs)>2 else R1+600
            S1 = all_lows[0] if len(all_lows)>0 else prev_low
            S2 = all_lows[1] if len(all_lows)>1 else S1+300
            S3 = all_lows[2] if len(all_lows)>2 else S1+600

            trend = "🟢 Өсүү канал" if lows[-1] > lows[-10] else "🔴 Түшүү канал" if highs[-1] < highs[-10] else "⚪️ Консолидация"
            whale = f"🐋 КИТ {vol_ratio:.1f}x!" if vol_ratio>1.8 else f"🐳 {vol_ratio:.1f}x" if vol_ratio>1.3 else f"🦈 {vol_ratio:.1f}x норм"
            pos = (last_close - min(lows[-40:])) / (max(highs[-40:]) - min(lows[-40:]))*100 if max(highs[-40:])!=min(lows[-40:]) else 50

            bishkek = datetime.now(timezone.utc) + timedelta(hours=6)
            t = bishkek.strftime("%H:%M")

            signal = None
            if last_close > prev_high:
                signal = f"🚀 LONG BOS СЫНДЫ!\nБаа: ${last_close:,.0f} > R ${prev_high:,.0f}\n{whale} | {trend}"
            elif last_close < prev_low:
                signal = f"🚀 SHORT BOS СЫНДЫ!\nБаа: ${last_close:,.0f} < S ${prev_low:,.0f}\n{whale} | {trend}"

            if signal and signal!= last_signal:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": signal})
                last_signal = signal
            else:
                if time.time() - last_hourly > 3600:
                    txt = f"""💎 BTC PRO S/R | {t} Bishkek

💰 АЗЫР БАА: ${last_close:,.2f}
🏦 Bybit: ${last_close:,.2f} | {whale}

🔴 RESISTANCE:
R3: ${R3:,.0f} 🔥 Күчтүү
R2: ${R2:,.0f} ⚠️ Орточо
R1: ${R1:,.0f} → BOS чекит LONG

🟢 SUPPORT:
S1: ${S1:,.0f} → BOS чекит SHORT
S2: ${S2:,.0f} ⚠️ Орточо
S3: ${S3:,.0f} 🔥 Күчтүү OB

📈 {trend} | Вайкофф {pos:.0f}%
BOS: >${prev_high:,.0f} LONG | <${prev_low:,.0f} SHORT

⚡️ Akyl Pro"""
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": txt})
                    last_hourly = time.time()
                    print(f"📤 Hourly S/R {last_close}", flush=True)
        except Exception as e:
            print(f"Loop ERR {e}", flush=True)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
