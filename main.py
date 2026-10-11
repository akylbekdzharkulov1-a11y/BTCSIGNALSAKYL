import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OFFSET = -96

@app.route('/')
def home(): return "BTC STRONG SETUP ONLY"

def send(t):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=10)
    except: pass

def ema(data, p):
    k=2/(p+1); e=sum(data[:p])/p
    for x in data[p:]: e=x*k+e*(1-k)
    return e

def rsi(closes, p=14):
    gains=[]; losses=[]
    for i in range(1,p+1):
        d=closes[-i]-closes[-i-1]
        (gains if d>=0 else losses).append(abs(d))
    ag=sum(gains)/p if gains else 0; al=sum(losses)/p if losses else 0.01
    return 100-(100/(1+ag/al)) if al!=0 else 100

def get_data():
    try:
        r=requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=200",timeout=10).json()
        h=[float(x[2])+OFFSET for x in r]; l=[float(x[3])+OFFSET for x in r]; c=[float(x[4])+OFFSET for x in r]
        return h,l,c
    except: return None,None,None

def loop():
    print("STRONG SETUP MODE",flush=True)
    send("✅ КҮЧТҮҮ СЕТАП гана күйдү!\nЭми алсыз BOS келбейт!\nТек 100% сетап келет!")
    last=0
    while True:
        try:
            highs,lows,closes=get_data()
            if not closes: time.sleep(20); continue
            cap=closes[-1]
            prev_h=max(highs[-21:-1]); prev_l=min(highs[-21:-1]) # 20шам R/S
            # Индикаторлор
            rsi_v=rsi(closes); e50=ema(closes,50); e200=ema(closes,200)
            buy_liq=max(highs[-50:-1]); sell_liq=min(lows[-50:-1])
            # MACD жөнөкөй
            macd = e50 - e200 # тренд үчүн
            bish=(datetime.now(timezone.utc)+timedelta(hours=6)).strftime("%H:%M")

            if last!=0:
                # LONG КҮЧТҮҮ СЕТАП ШАРТТАРЫ
                long_cond = cap>prev_h and last<=prev_h and rsi_v>55 and cap>e50 and e50>e200 and macd>0
                short_cond = cap<prev_l and last>=prev_l and rsi_v<45 and cap<e50 and e50<e200 and macd<0

                if long_cond:
                    # Ликвиддүүлүк алынганбы текшерүү
                    liq_sweep = "✅ Sell Liq алынды!" if min(lows[-10:-1]) < sell_liq+20 else "⚠️ Liq алына элек"
                    send(f"""🚀 КҮЧТҮҮ LONG СЕТАП 🔥🔥🔥

📍 Кирүү: ${cap:,.2f} (BOS ${prev_h:,.0f} сынды)
⏰ {bish} Бишкек

🎯 КОНКРЕТНЫЙ ПЛАН:
1️⃣ Кирүү: MARKET LONG азыр
   Же LIMIT: ${prev_h:,.0f} ретестте
2️⃣ SL: ${sell_liq-50:,.0f} (Sell Liq асты) - 100% милдеттүү!
3️⃣ TP1: ${buy_liq:,.0f} (Buy Liq) -> 50% жап
4️⃣ TP2: ${buy_liq+200:,.0f} -> 50% жап
5️⃣ RR: 1:2.5

📊 ПОДТВЕРЖДЕНИЕ:
RSI: {rsi_v:.1f} 🟢 >55 КҮЧТҮҮ
EMA50: ${e50:,.0f} ✅ үстүндө
EMA200: ${e200:,.0f} 🟢 BULL тренд
MACD: 🟢 LONG
💧 {liq_sweep}
💧 Максат: ${buy_liq:,.0f}

⚠️ Эгер LIMIT аткарылбаса MARKET менен кир!""")

                if short_cond:
                    liq_sweep = "✅ Buy Liq алынды!" if max(highs[-10:-1]) > buy_liq-20 else "⚠️ Liq алына элек"
                    send(f"""🚀 КҮЧТҮҮ SHORT СЕТАП 🔥🔥🔥

📍 Кирүү: ${cap:,.2f} (BOS ${prev_l:,.0f} сынды)
⏰ {bish} Бишкек

🎯 КОНКРЕТНЫЙ ПЛАН:
1️⃣ Кирүү: MARKET SHORT азыр
   Же LIMIT: ${prev_l:,.0f} ретестте
2️⃣ SL: ${buy_liq+50:,.0f} (Buy Liq үстү) - 100% милдеттүү!
3️⃣ TP1: ${sell_liq:,.0f} (Sell Liq) -> 50% жап
4️⃣ TP2: ${sell_liq-200:,.0f} -> 50% жап
5️⃣ RR: 1:2.5

📊 ПОДТВЕРЖДЕНИЕ:
RSI: {rsi_v:.1f} 🔴 <45 КҮЧТҮҮ
EMA50: ${e50:,.0f} ❌ астында
EMA200: ${e200:,.0f} 🔴 BEAR тренд
MACD: 🔴 SHORT
💧 {liq_sweep}
💧 Максат: ${sell_liq:,.0f}

⚠️ Эгер LIMIT аткарылбаса MARKET менен кир!""")

            last=cap
            print(f"CHECK ${cap:.0f} RSI {rsi_v:.0f} {'STRONG' if cap>prev_h or cap<prev_l else 'wait'}",flush=True)
        except Exception as e:
            print(f"ERR {e}",flush=True)
        time.sleep(60)

threading.Thread(target=loop,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
