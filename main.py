from flask import Flask
import os, time, requests, threading, statistics
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route('/')
def home(): return "BTC PRO S/R BINANCE LIVE ✅"

def get_candles():
    # 1. Binance аракет
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=100"
        r = requests.get(url, timeout=10)
        data = r.json()
        # [openTime, open, high, low, close, volume...]
        return [(float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in data]
    except Exception as e:
        print(f"Binance fail {e}", flush=True)
    # 2. Bybit запас
    try:
        url = "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=15&limit=100"
        r = requests.get(url, timeout=10).json()
        d = r['result']['list'][::-1]
        return [(float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in d]
    except Exception as e:
        print(f"Bybit fail {e}", flush=True)
    return None

def bot_loop():
    print("✅ BINANCE PRO S/R STARTED", flush=True)
    last_signal = ""
    last_hourly = 0
    while True:
        try:
            candles = get_candles()
            if not candles or len(candles)<40:
                print("No candles, wait 30s", flush=True)
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

            all_highs = sorted(set([int(h) for h in highs[-50:]]), reverse=True)
            all_lows = sorted(set([int(l) for l in lows[-50:]]))
            R1,R2,R3 = all_highs[0], all_highs[1] if len(all_highs)>1 else all_highs[0]+300, all_highs[2] if len(all_highs)>2 else all_highs[0]+600
            S1,S2,S3 = all_lows[0], all_lows[1] if len(all_lows)>1 else all_lows[0]-300, all_lows[2] if len(all_lows)>2 else all_lows[0]-600

            bishkek = datetime.now(timezone.utc) + timedelta(hours=6)
            t = bishkek.strftime("%H:%M")

            print(f"DEBUG price=${last_close} BOS H:{prev_high} L:{prev_low} Vol:{vol_ratio:.1f}x", flush=True)

            signal = None
            if last_close > prev_high:
                signal = f"🚀 LONG BOS!\n${last_close:,.0f} > R ${prev_high:,.0f}"
            elif last_close < prev_low:
                signal = f"🚀 SHORT BOS!\n${last_close:,.0f} < S ${prev_low:,.0f}"

            if signal and signal!= last_signal:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": signal})
                last_signal = signal
            else:
                if time.time() - last_hourly > 3600:
                    txt = f"""💎 BTC PRO S/R | {t} | Binance 15m

💰 АЗЫР БАА: ${last_close:,.2f}
🏦 Байбит/Бинанс: ${last_close:,.2f} | Кит {vol_ratio:.1f}x

🔴 RESISTANCE:
R3: ${R3:,.0f} 🔥
R2: ${R2:,.0f} ⚠️
R1: ${R1:,.0f} → LONG BOS

🟢 SUPPORT:
S1: ${S1:,.0f} → SHORT BOS
S2: ${S2:,.0f}
S3: ${S3:,.0f} 🔥

BOS: >${prev_high:,.0f} | <${prev_low:,.0f}
⚡️ Akyl"""
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": txt})
                    last_hourly = time.time()

        except Exception as e:
            print(f"Loop ERR {e}", flush=True)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
