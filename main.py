import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OFFSET = -96

@app.route('/')
def home(): return "BTC PRO BOS RSI MACD EMA LIQ"

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=10)
    except: pass

def ema(data, period):
    k = 2/(period+1)
    ema_val = sum(data[:period])/period
    for price in data[period:]:
        ema_val = price*k + ema_val*(1-k)
    return ema_val

def rsi(closes, period=14):
    if len(closes) < period+1: return 50
    gains, losses = [], []
    for i in range(1, period+1):
        diff = closes[-i] - closes[-i-1]
        if diff >=0: gains.append(diff)
        else: losses.append(abs(diff))
    avg_gain = sum(gains)/period if gains else 0
    avg_loss = sum(losses)/period if losses else 0.01
    if avg_loss==0: return 100
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

def macd(closes):
    if len(closes) < 35: return 0,0
    e12 = ema(closes, 12)
    e26 = ema(closes, 26)
    macd_line = e12 - e26
    # signal ema 9 of macd - жөнөкөйлөтүп акыркы 9 macd
    macd_hist = closes[-9:]
    # сигнал үчүн акыркы 9 жабылуунун ema айырмасы
    return macd_line, macd_line - ema(closes[-18:], 9)

def get_candles():
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=200", timeout=15).json()
        highs = [float(x[2])+OFFSET for x in r]
        lows = [float(x[3])+OFFSET for x in r]
        closes = [float(x[4])+OFFSET for x in r]
        return highs, lows, closes
    except: return None, None, None

def loop():
    print("PRO BOT START", flush=True)
    send("✅ PRO BOS күйдү!\nRSI + MACD + EMA 50/200 + Ликвидность кошулду!\nЭми BOS күчтүү сигнал менен келет!")
    last_price = 0
    while True:
        try:
            highs, lows, closes = get_candles()
            if closes is None: time.sleep(20); continue
            cap = closes[-1]
            prev_h = max(highs[-21:-1])
            prev_l = min(lows[-21:-1])

            # Индикаторлор
            rsi_val = rsi(closes)
            ema50 = ema(closes, 50)
            ema200 = ema(closes, 200)
            macd_line, hist = macd(closes)

            # Ликвидность
            buy_liq = max(highs[-50:-1]) # Buy Side Liquidity
            sell_liq = min(lows[-50:-1]) # Sell Side Liquidity

            # Тренд
            trend = "🟢 BULL" if cap > ema200 and ema50 > ema200 else "🔴 BEAR" if cap < ema200 else "⚪️ RANGE"
            macd_trend = "🟢 LONG" if macd_line > 0 and hist > 0 else "🔴 SHORT" if macd_line < 0 else "⚪️"

            print(f"Cap ${cap:.0f} RSI {rsi_val:.0f} {trend}", flush=True)

            if last_price!= 0:
                bish = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%H:%M")
                # LONG BOS
                if cap > prev_h and last_price <= prev_h:
                    # Фильтр: RSI 50 дөн жогору + EMA дан жогору болсо гана күчтүү
                    strong = "🔥 КҮЧТҮҮ LONG" if rsi_val > 55 and cap > ema50 and macd_line > 0 else "⚠️ Алсыз LONG"
                    send(f"""🚀 BOS LONG! {strong}

💰 Capital: ${cap:,.2f} > R ${prev_h:,.0f}
🕐 {bish} Бишкек

📊 ИНДИКАТОРЛОР:
RSI(14): {rsi_val:.1f} {'🟢' if rsi_val>55 else '🔴' if rsi_val<45 else '⚪️'} {'OVERBOUGHT!' if rsi_val>70 else 'OVERSOLD' if rsi_val<30 else ''}
MACD: {macd_line:.1f} {macd_trend}
EMA50: ${ema50:,.0f} {'✅ үстүндө' if cap>ema50 else '❌ астында'}
EMA200: ${ema200:,.0f} {trend}
💧 Ликвидность:
Buy Liq: ${buy_liq:,.0f} 🎯
Sell Liq: ${sell_liq:,.0f}

СЕТАП: LONG SL ${prev_l-80:,.0f} TP ${cap+150:,.0f} / ${cap+300:,.0f}""")

                # SHORT BOS
                if cap < prev_l and last_price >= prev_l:
                    strong = "🔥 КҮЧТҮҮ SHORT" if rsi_val < 45 and cap < ema50 and macd_line < 0 else "⚠️ Алсыз SHORT"
                    send(f"""🚀 BOS SHORT! {strong}

💰 Capital: ${cap:,.2f} < S ${prev_l:,.0f}
🕐 {bish} Бишкек

📊 ИНДИКАТОРЛОР:
RSI(14): {rsi_val:.1f} {'🔴' if rsi_val<45 else '🟢' if rsi_val>55 else '⚪️'} {'OVERSOLD!' if rsi_val<30 else 'OVERBOUGHT' if rsi_val>70 else ''}
MACD: {macd_line:.1f} {macd_trend}
EMA50: ${ema50:,.0f} {'❌ астында' if cap<ema50 else '✅ үстүндө'}
EMA200: ${ema200:,.0f} {trend}
💧 Ликвидность:
Buy Liq: ${buy_liq:,.0f}
Sell Liq: ${sell_liq:,.0f} 🎯

СЕТАП: SHORT SL ${prev_h+80:,.0f} TP ${cap-150:,.0f} / ${cap-300:,.0f}""")

            last_price = cap
        except Exception as e:
            print(f"ERR {e}", flush=True)
        time.sleep(60)

threading.Thread(target=loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
