import os, time, threading, requests
from flask import Flask
TOKEN=os.getenv("BOT_TOKEN")
CHANNEL="@btcsignalakyl1"
app=Flask(__name__)
@app.route('/')
def home(): return "BTC FUTURES LIVE"
LAST=0
def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id":CHANNEL,"text":m,"parse_mode":"HTML"},timeout=10)
    except: pass
def get_candles(sym="BTCUSDT",interval="5m",limit=100):
    url=f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={interval}&limit={limit}"
    r=requests.get(url,timeout=10).json()
    closes=[float(x[4]) for x in r]
    highs=[float(x[2]) for x in r]
    lows=[float(x[3]) for x in r]
    return closes,highs,lows
def rsi(c,p=14):
    if len(c)<p+1: return 50
    g=l=0
    for i in range(1,p+1):
        d=c[-i]-c[-i-1]
        if d>0: g+=d
        else: l+=abs(d)
    if l==0: return 70
    return 100-(100/(1+(g/p)/(l/p)))
def loop():
    global LAST
    print("FUTURES STARTED",flush=True)
    while True:
        try:
            c5,h5,l5=get_candles("BTCUSDT","5m",100)
            if len(c5)<60:
                time.sleep(10); continue
            price=c5[-1]
            ema20=sum(c5[-20:])/20
            ema50=sum(c5[-50:])/50
            rr=rsi(c5)
            ah=max(h5[-72:-12])
            al=min(l5[-72:-12])
            ph=c5[-2]<ah and price>ah
            pl=c5[-2]>al and price<al
            s_sell=int(ph)+int(ema20<ema50)+int(rr<58)
            s_buy=int(pl)+int(ema20>ema50)+int(rr>42)
            sig="SELL" if s_sell>=2 else "BUY" if s_buy>=2 else None
            print(f"CHECK {price:.0f} FUTURES RSI {rr:.0f} B:{s_buy} S:{s_sell} {sig}",flush=True)
            if sig and time.time()-LAST>1800:
                sl=ah+120 if sig=="SELL" else al-120
                tp=al if sig=="SELL" else ah
                icon="🔴" if sig=="SELL" else "🟢"
                send(f"{icon} <b>BTCUSDT FUTURES {sig} {price:.2f}</b>\nScore: {max(s_sell,s_buy)}/3 RSI:{rr:.0f}\nSL:{sl:.1f} TP:{tp:.1f}\n#futures")
                LAST=time.time()
            time.sleep(60)
        except Exception as e:
            print(f"ERR {e}",flush=True); time.sleep(30)
threading.Thread(target=loop,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
