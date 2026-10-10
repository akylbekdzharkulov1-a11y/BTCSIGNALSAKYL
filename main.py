from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"
def run_web():
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()
import os, time, requests
from datetime import datetime, timezone, timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN"); CHAT_ID=os.getenv("CHAT_ID")
BISHKEK=timezone(timedelta(hours=6))
def send(t):
 try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={"chat_id":CHAT_ID,"text":t,"parse_mode":"HTML"},timeout=10)
 except: pass
def price():
 try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()['price'])
 except: return None
def kl(tf):
 try:
  r=requests.get(f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={tf}&limit=20",timeout=10).json()
  return [float(x[4]) for x in r],[float(x[2]) for x in r],[float(x[3]) for x in r]
 except: return None,None,None
send("✅ <b>BTCSIGNALS AKYL иштеп баштады!</b>\nАр 15 мүнөттө BTC отчет келет.")
while True:
 try:
  p=price(); c15,h15,l15=kl("15m"); c1h,_,_=kl("1h"); c4h,_,_=kl("4h")
  if not p or not c15: time.sleep(30); continue
  now=datetime.now(BISHKEK)
  bos="BULLISH 🚀" if p>max(h15[-10:-1]) else "BEARISH 🔻" if p<min(l15[-10:-1]) else "RANGE ⏳"
  kill="NY 17-20 🔥" if 17<=now.hour<=20 else "LDN 12-16 ⚡" if 12<=now.hour<=16 else f"OFF {now.hour}:00"
  send(f"<b>₿ BTC | {now.strftime('%H:%M')}</b>\n💰 <b>${p:,.2f}</b>\n<b>15M:</b> {bos}\n<b>1H:</b> {'UP' if c1h[-1]>c1h[-5] else 'DOWN'} | <b>4H:</b> {'Markup' if c4h[-1]>c4h[-5] else 'Markdown'}\n<b>{kill}</b>\n🎯 FVG+OB күт")
 except Exception as e: print(e)
 time.sleep(900)
