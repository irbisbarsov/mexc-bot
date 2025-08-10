import os
import time
import requests
import hmac
import hashlib
from decimal import Decimal, ROUND_DOWN
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Получаем ключи
API_KEY = os.getenv("MEXC_API_KEY", "").strip()
API_SECRET = os.getenv("MEXC_API_SECRET", "").strip()

if not API_KEY or not API_SECRET:
    print("❌ Не заданы API ключи")
    exit()

SYMBOL = "KASUSDT"
QUANTITY = 10

def round_down(price, precision=4):
    p = Decimal(str(price))
    return float(p.quantize(Decimal(f"1e-{precision}"), rounding=ROUND_DOWN))

def get_price():
    try:
        r = requests.get("https://api.mexc.com/api/v3/ticker/price", params={"symbol": SYMBOL})
        return float(r.json()['price'])
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def get_server_time():
    try:
        r = requests.get("https://api.mexc.com/api/v3/time")
        return r.json()['serverTime']
    except:
        return int(time.time() * 1000)

def sign_request(params):
    params["timestamp"] = get_server_time()
    sorted_items = sorted(params.items())
    query_string = '&'.join(f"{k}={v}" for k, v in sorted_items)
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    return params

def create_limit_buy(price):
    params = {
        "symbol": SYMBOL,
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": str(QUANTITY),
        "price": str(round_down(price))
    }
    signed = sign_request(params)
    payload = '&'.join(f"{k}={v}" for k, v in sorted(signed.items()))
    
    headers = {
        "X-MEXC-APIKEY": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    r = requests.post(
        "https://api.mexc.com/api/v3/order",
        headers=headers,
        data=payload.encode('utf-8')
    )
    
    print(f"📨 Ответ: {r.status_code} {r.text}")
    if r.status_code == 200:
        try:
            data = r.json()
            if data.get('code') == '200':
                print(f"✅ Куплено по: {data['price']}")
                return data['orderId']
            else:
                print(f"❌ Ошибка API: {data}")
        except:
            print(f"❌ Не JSON: {r.text}")
    return None

# === ЗАПУСК ===
if __name__ == "__main__":
    print("🚀 Бот запущен...")
    current_price = get_price()
    if not current_price:
        print("❌ Не удалось получить цену")
        exit()
    
    buy_price = current_price * 0.995
    print(f"📊 Текущая цена: {current_price:.6f}")
    print(f"🛒 Ставим лимит на покупку: {buy_price:.6f}")
    
     order_id = create_limit_buy(buy_price)
    if order_id:
        print(f"🎉 Ордер выставлен: {order_id}")
    else:
        print("❌ Не удалось выставить ордер")


      
        print("❌ Не удалось выставить ордер")
