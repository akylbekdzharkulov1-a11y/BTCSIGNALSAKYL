from flask import Flask
import os, time, requests, threading, statistics
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route('/')
def home(): return "BTC PRO Whale Wyckoff ✅"

def get_candles():
    try:
        url = "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=15&limit=50"
        r = requests.get(url, timeout=10).json()
        data = r['result']['list'][::-1]
        # [start, open, high, low, close, volume, turnover]
        return [(float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in data]
    except Exception as e:
        print(f"ERR {e}", flush=True)
        return None

def bot_loop():
    print("✅ PRO MODE Whale+Wyckoff", flush=True)
    last_signal = ""
    last_hourly = 0
    while True:
        try:
            candles = get_candles()
            if not candles or len(candles)<25:
                time.sleep(60); continue

            opens = [c[0] for c in candles]
            highs = [c[1] for c in candles]
            lows = [c[2] for c in candles]
            closes = [c[3] for c in candles]
            volumes = [c[4] for c in candles]

            last_close = closes[-1]
            last_vol = volumes[-1]
            avg_vol = statistics.mean(volumes[-21:-1])
            vol_ratio = last_vol / avg_vol if avg_vol>0 else 1

            prev_high = max(highs[-21:-1])
            prev_low = min(lows[-21:-1])
            range_high = max(highs[-25:])
            range_low = min(lows[-25:])

            # Тренд линиялар
            # Support тренд - lows өсүп жатабы?
            support_slope = lows[-1] - lows[-10]
            resist_slope = highs[-1] - highs[-10]
            if support_slope > 0 and resist_slope > 0:
                trend_line = "📈 Өсүүчү канал (Higher Highs & Higher Lows) - Тренд линия өйдө"
                trend = "🟢 Uptrend"
            elif support_slope < 0 and resist_slope < 0:
                trend_line = "📉 Түшүүчү канал (Lower Highs & Lower Lows) - Тренд линия ылдый"
                trend = "🔴 Downtrend"
            else:
                trend_line = "📊 Горизонтал канал - Консолидация, тренд линиялар жакындашууда"
                trend = "⚪️ Range"

            # Кит анализ
            if vol_ratio > 2.0 and abs(closes[-1]-opens[-1]) > (prev_high-prev_low)*0.3:
                whale = f"🐋 КИТ АКТИВ! Объем {vol_ratio:.1f}x көп! Чоң оюнчу кирди! Vol: ${last_vol:,.0f}"
            elif vol_ratio > 1.5:
                whale = f"🐳 Чоң объем {vol_ratio:.1f}x - Интерес өстү, Vol: ${last_vol:,.0f}"
            else:
                whale = f"🦈 Объем нормалдуу {vol_ratio:.1f}x - Кит жок, ритейл соода, Vol: ${last_vol:,.0f}"

            # Вайкофф фаза
            pos_in_range = (last_close - range_low) / (range_high - range_low) if range_high!=range_low else 0.5
            if pos_in_range < 0.3 and vol_ratio > 1.3:
                wyckoff = "🔵 Вайкофф: Аккумуляция (Киттер топтоп жатат, Spring фазасы мүмкүн)"
            elif pos_in_range > 0.7 and vol_ratio > 1.3:
                wyckoff = "🟣 Вайкофф: Дистрибуция (Киттер сатып жатат, Upthrust фазасы)"
            elif pos_in_range < 0.5:
                wyckoff = "🟡 Вайкофф: Ретест / LPS - Колдоо текшерилип жатат"
            else:
                wyckoff = "🟠 Вайкофф: Markup - Өсүү уланууда, FOMO фазасы"

            # RSI жөнөкөй
            gains = [max(0, closes[i]-closes[i-1]) for i in range(1,len(closes))]
            losses = [max(0, closes[i-1]-closes[i]) for i in range(1,len(closes))]
            avg_gain = statistics.mean(gains[-14:]) if gains else 0
            avg_loss = statistics.mean(losses[-14:]) if losses else 1
            rsi = 100 - (100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 70
            rsi_txt = f"RSI {rsi:.0f} - Перекуплен" if rsi>70 else f"RSI {rsi:.0f} - Перепродан" if rsi<30 else f"RSI {rsi:.0f} - Нейтрал"

            bishkek = datetime.now(timezone.utc) + timedelta(hours=6)
            t = bishkek.strftime("%d.%m %H:%M")

            # Сигнал
            signal = None
            if last_close > prev_high:
                entry = last_close
                sl = min(lows[-5:])
                tp1 = entry + (entry - sl)*1.5
                tp2 = entry + (entry - sl)*3
                signal = f"""🚀 SMC PRO SIGNAL 🟢 LONG | {t}

💰 АЗЫР БАА: ${entry:,.2f}
🏦 Bybit: ${entry:,.2f} | Vol: ${last_vol:,.0f} ({vol_ratio:.1f}x)

📈 ТРЕНД ЛИНИЯ:
{trend_line}
BOS {prev_high:,.0f} сынды - Структура бузулду!

{whale}

📊 ОБЪЕМ АНАЛИЗ:
- Учурдагы: ${last_vol:,.0f} vs Орточо: ${avg_vol:,.0f}
- {rsi_txt}
- Order Flow: Покупатели доминируют

{wyckoff}

🔹 Вход: ${entry:,.2f}
🔻 SL: ${sl:,.2f} (OB асты)
🎯 TP1: ${tp1:,.2f} | TP2: ${tp2:,.2f}

⚡️ Akyl Whale SMC"""
            elif last_close < prev_low:
                entry = last_close
                sl = max(highs[-5:])
                tp1 = entry - (sl-entry)*1.5
                tp2 = entry - (sl-entry)*3
                signal = f"""🚀 SMC PRO SIGNAL 🔴 SHORT | {t}

💰 АЗЫР БАА: ${entry:,.2f}
🏦 Bybit: ${entry:,.2f} | Vol: ${last_vol:,.0f} ({vol_ratio:.1f}x)

📉 ТРЕНД ЛИНИЯ:
{trend_line}
BOS {prev_low:,.0f} сынды!

{whale}

📊 ОБЪЕМ АНАЛИЗ:
- Учурдагы: ${last_vol:,.0f} vs Орточо: ${avg_vol:,.0f}
- {rsi_txt}
- Order Flow: Продавцы доминируют

{wyckoff}

🔹 Вход: ${entry:,.2f}
🔻 SL: ${sl:,.2f} (OB үстү)
🎯 TP1: ${tp1:,.2f} | TP2: ${tp2:,.2f}

⚡️ Akyl Whale SMC"""

            if signal and signal!= last_signal:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": signal})
                last_signal = signal
            else:
                if time.time() - last_hourly > 3600:
                    txt = f"""💎 BTC PRO АНАЛИЗ | {t} Bishkek | 15m

💰 АЗЫР БАА: ${last_close:,.2f}
🏦 Байбит: ${last_close:,.2f}
📊 ТрейдингВью: {max(highs[-1:]):,.0f} / {min(lows[-1:]):,.0f}

📈 ТРЕНД ЛИНИЯЛАР:
{trend_line}
- Сопротивление: ${prev_high:,.0f} (BOS LONG)
- Поддержка: ${prev_low:,.0f} (BOS SHORT)
- Канал: ${range_low:,.0f} - ${range_high:,.0f}

{whale}

📊 ОБЪЕМ:
- Азыр: ${last_vol:,.0f} | Орточо 20 свеча: ${avg_vol:,.0f} | К: {vol_ratio:.1f}x
- {rsi_txt}

🧠 ВАЙКОФФ + СТРУКТУРА:
{wyckoff}
- Фаза позициясы: {pos_in_range*100:.0f}% диапазона
- {trend}

⏳ Күтүү - BOS + Кит подтвержение күтөм!

⚡️ Akyl Professional"""
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": txt})
                    last_hourly = time.time()

        except Exception as e:
            print(f"❌ {e}", flush=True)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
