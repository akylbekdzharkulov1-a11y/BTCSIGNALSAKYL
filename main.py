from flask import Flask
import os, time, requests, threading
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive"

def get_btc_price():
    try:
        # 1-аракет CoinGecko
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
        return float(r['bitcoin']['usd'])
    except:
        try:
            # 2-аракет Binance
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
            return float(r['price'])
        except:
            return 114500.00 # запас баа

def bot_loop():
    token=os.environ.get("BOT_TOKEN"); chat=os.environ.get("CHAT_ID")
    print(f"✅ BOT STARTED chat={chat}", flush=True)
    while True:
        try:
            p=get_btc_price()
            txt=f"✅ BTCSIGNALS AKYL\n\n💰 BTC: ${p:,.2f}\n📈 Тренд: LONG - Liquidity Sweep\n⏰ {time.strftime('%H:%M')} Bishkek\n\nКанал: {chat}"
            r=requests.post(f"https://api.telegram.org/bot{token}/sendMessage",data={"chat_id":chat,"text":txt}, timeout=10)
            print(f"📤 {r.status_code} {r.text[:150]}", flush=True)
        except Exception as e:
            print(f"❌ {e}", flush=True)
        time.sleep(900)

threading.Thread(target=bot_loop,daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
