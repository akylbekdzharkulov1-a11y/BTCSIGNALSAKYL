import os, time, threading, requests, math
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@btcsignalakyl1"
app = Flask(__name__)
@app.route('/')
def home(): return "BTC FUTURES AMD PRO LIVE"
LAST_SIGNAL = 0

def send(msg):
    if not TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHANNEL, "text": msg, "parse_mode":"HTML", "disable_web_page_preview": True}, timeout=10)
    except: pass

def get_futures_candles(symbol="BTCUSDT", interval="5m", limit=100):
    # Binance Futures - чыныгы фьючерс баасы
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        r = requests.get(url, timeout=10).json()
        closes = [float(x[4]) for x in r]
        highs = [float(x[2]) for x in r]
        lows = [float(x[3]) for x in r]
        volumes = [float(x[5]) for x in r]
        return closes, highs, lows, volumes
    except Exception as e:
        print(f"price err {e}", flush=True)
        return [], [], [], []

def rsi_calc(closes, period=14):
    if len(closes)<period+1: return 50
    gains=losses=0
    for i in range(1, period+1):
        d=closes[-i]-closes[-i-1]
        if d>0: gains+=d
        else: losses+=abs(d)
    if losses==0: return 70
    rs=(gains/period)/(losses/period)
    return 100-(100/(1+rs))

def loop():
    global LAST_SIGNAL
    print("FUTURES AMD STARTED", flush=True)
    while True:
        try:
            c5, h5, l5, v5 = get_futures_candles("BTCUSDT", "5m", 100)
            c15, _, _, _ = get_futures_candles("BTCUSDT", "15m", 100)
            if len(c5)<60:
                time.sleep(30); continue

            price=c5[-1]
            ema20=sum(c5[-20:])/20
            ema50=sum(c5[-50:])/50
            rsi=rsi_calc(c5)

            # Asia session high/low (фьючерс)
            asia_h=max(h5[-72:-12]) if len(h5)>80 else max(h5)
            asia_l=min(l5[-72:-12]) if len(l5)>80 else min(l5)

            prev=c5[-2]
            sweep_high=prev<asia_h and price>asia_h
            sweep_low=prev>asia_l and price<asia_l

            score_sell=int(sweep_high)+int(ema20<ema50)+int(price<asia_h-(asia_h-asia_l)*0.3)+int(rsi<58)
            score_buy=int(sweep_low)+int(ema20>ema50)+int(price>asia_l+(asia_h-asia_l)*0.3)+int(rsi>42)

            sig=None
            if score_sell>=3: sig="SELL"
            if score_buy>=3: sig="BUY"

            # 1 саатта бир жолу гана сигнал
            if sig and time.time()-LAST_SIGNAL>3600:
                sl=asia_h+120 if sig=="SELL" else asia_l-120
                tp=asia_l if sig=="SELL" else asia_h
                icon="🔴" if sig=="SELL" else "🟢"
                msg=(f"{icon} <b>BTCUSDT FUTURES {sig} {price:.2f}</b>\n\n"
                     f"Score: {max(score_sell,score_buy)}/4 | RSI: {rsi:.1f}\n"
                     f"EMA20: {ema20:.1f} EMA50: {ema50:.1f}\n"
                     f"Asia H: {asia_h:.1f} L: {asia_l:.1f}\n"
                     f"SL: {sl:.2f} TP: {tp:.2f}\n\n#futures #BTC")
                send(msg)
                LAST_SIGNAL=time.time()
                print(f"SENT {sig} {price}", flush=True)

            time.sleep(60)
        except Exception as e:
            print(f"loop err {e}", flush=True)
            time.sleep(60)

threading.Thread
