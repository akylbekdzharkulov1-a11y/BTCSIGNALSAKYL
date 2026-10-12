import os, time, threading, requests
from flask import Flask
import math

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@btcsignalakyl"  # өзүңдүн BTC канал
SYMBOL = "BTC-USD"
app = Flask(__name__)
LAST_SIGNAL = 0

def send(msg):
    if not TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHANNEL, "text": msg, "parse_mode":"HTML", "disable_web_page_preview": True}, timeout=10)
    except: pass

def get_candles():
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=15m&range=5d"
        j = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
        res = j['chart']['result'][0]
        closes = [c for c in res['indicators']['quote'][0]['close'] if c is not None]
        volumes = [v for v in res['indicators']['quote'][0]['volume'] if v is not None]
        return closes, volumes
    except Exception as e:
        print(f"price err {e}", flush=True)
        return None, None

def ema(data, n):
    if len(data)<n: return sum(data)/len(data)
    k=2/(n+1); e=sum(data[:n])/n
    for p in data[n:]: e = p*k + e*(1-k)
    return e

def rsi(data, n=14):
    gains=losses=0
    for i in range(1,n+1):
        d=data[-i]-data[-i-1]
        if d>0: gains+=d
        else: losses-=d
    if losses==0: return 70
    rs=(gains/n)/(losses/n)
    return 100-(100/(1+rs))

def check_pro(closes, volumes):
    price=closes[-1]
    ema20=ema(closes,20)
    ema50=ema(closes,50)
    ema200=ema(closes,200)
    r=rsi(closes)
    
    # MACD
    ema12=ema(closes,12); ema26=ema(closes,26)
    macd=ema12-ema26
    macd_prev=ema(closes[:-1],12)-ema(closes[:-1],26)
    
    # Bollinger
    sma20=sum(closes[-20:])/20
    std=math.sqrt(sum((x-sma20)**2 for x in closes[-20:])/20)
    bb_low=sma20-2*std; bb_high=sma20+2*std
    
    # ATR for SL/TP
    atr=sum(abs(closes[i]-closes[i-1]) for i in range(-14,0))/14
    
    buy=0; sell=0; reasons=[]
    
    # 1. Тренд (күчтүү)
    if price>ema20>ema50>ema200: buy+=2; reasons.append("🚀 Супер өйдө тренд")
    elif price>ema20 and ema20>ema50: buy+=1; reasons.append("Өйдө тренд")
    if price<ema20<ema50<ema200: sell+=2; reasons.append("🔻 Супер ылдый тренд")
    elif price<ema20 and ema20<ema50: sell+=1; reasons.append("Ылдый тренд")
    
    # 2. RSI
    if 50<r<68: buy+=1; reasons.append(f"RSI {r:.0f} күч")
    if r>72: sell+=1; reasons.append(f"RSI {r:.0f} перекуп")
    if 32<r<50: sell+=1; reasons.append(f"RSI {r:.0f} алсыз")
    if r<30: buy+=1; reasons.append(f"RSI {r:.0f} перепродан - отскок!")
    
    # 3. MACD
    if macd>0 and macd>macd_prev: buy+=1; reasons.append("MACD өйдө")
    if macd<0 and macd<macd_prev: sell+=1; reasons.append("MACD ылдый")
    
    # 4. Bollinger + Liquidity Sweep
    if price<bb_low*1.001: buy+=1; reasons.append("BB астынан sweep")
    if price>bb_high*0.999: sell+=1; reasons.append("BB үстүнөн sweep")
    
    # 5. Volume
    if volumes and len(volumes)>20:
        avg_vol=sum(volumes[-20:])/20
        if volumes[-1]>avg_vol*1.3: 
            if buy>sell: reasons.append("🔥 Объем чоң BUY")
            else: reasons.append("🔥 Объем чоң SELL")

    return price, r, ema20, ema50, atr, buy, sell, reasons

def loop():
    global LAST_SIGNAL
    print("BTC PRO V2 STARTED", flush=True)
    time.sleep(15)
    while True:
        try:
            closes, vols = get_candles()
            if closes and len(closes)>200:
                price,rsi,ema20,ema50,atr,buy,sell,reasons = check_pro(closes, vols)
                side=None; score=0
                if buy>=4: side="BUY"; score=buy
                elif sell>=4: side="SELL"; score=sell
                
                print(f"CHECK ${price:.0f} RSI {rsi:.0f} B:{buy} S:{sell} {side}", flush=True)
                
                if side and (time.time()-LAST_SIGNAL)>5400: # 1.5 саатта 1 күчтүү сигнал
                    # Проф TP/SL
                    if side=="BUY":
                        sl=price-atr*1.5
                        tp1=price+atr*1.5
                        tp2=price+atr*3
                    else:
                        sl=price+atr*1.5
                        tp1=price-atr*1.5
                        tp2=price-atr*3
                    
                    emoji="🟢🟢🟢" if score>=5 else "🟢"
                    if side=="SELL": emoji="🔴🔴🔴" if score>=5 else "🔴"
                    
                    txt=f"<b>{emoji} BITCOIN {side} #{score}/6</b>\n\n"
                    txt+=f"<b>Price:</b> ${price:,.2f}\n"
                    txt+=f"<b>RSI:</b> {rsi:.1f} | <b>EMA20:</b> ${ema20:,.0f}\n\n"
                    txt+=f"<b>Анализ:</b>\n" + "\n".join([f"• {x}" for x in reasons[:4]]) + "\n\n"
                    txt+=f"<b>SL:</b> ${sl:,.2f} (-{abs(price-sl)/price*100:.2f}%)\n"
                    txt+=f"<b>TP1:</b> ${tp1:,.2f} (+{abs(tp1-price)/price*100:.2f}%)\n"
                    txt+=f"<b>TP2:</b> ${tp2:,.2f} (+{abs(tp2-price)/price*100:.2f}%)\n\n"
                    txt+=f"⏰ 15m | #BTC #BITCOIN"
                    
                    send(txt)
                    LAST_SIGNAL=time.time()
        except Exception as e:
            print(f"loop err {e}", flush=True)
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()

@app.route("/")
def home(): return "BTC PRO V2 Live"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
