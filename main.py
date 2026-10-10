from flask import Flask
import os, time, requests, threading
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive"
def bot_loop():
    token=os.environ.get("BOT_TOKEN"); chat=os.environ.get("CHAT_ID")
    print(f"✅ BOT STARTED chat={chat}", flush=True)
    while True:
        try:
            p=float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()['price'])
            txt=f"✅ BTCSIGNALS AKYL иштеп баштады!\n\n💰 BTC: ${p:,.2f}\nАр 15 мүнөттө BTC отчет келет."
            r=requests.post(f"https://api.telegram.org/bot{token}/sendMessage",data={"chat_id":chat,"text":txt})
            print(f"📤 {r.status_code} {r.text[:100]}", flush=True)
        except Exception as e: print(f"❌ {e}", flush=True)
        time.sleep(900)
threading.Thread(target=bot_loop,daemon=True).start()
if __name__=="__main__": app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
