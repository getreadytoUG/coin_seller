import time
import requests

from apis import wait_buy_filled
from utils import decide_buy, make_jwt_token

def place_market_buy(access_key, secret_key, market, price):
    """
    market: 예) 'KRW-BTC', 'USDT-BTC'
    price: 사용 금액 (KRW or USDT)
    """
    params = {
        "market": market,
        "side": "bid",
        "ord_type": "price",
        "price": price,
    }
    
    correct_flag = False
    for _ in range(3):
        try:
            jwt_token, params = make_jwt_token(access_key, secret_key, params)
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/json"
            }
            
            response = requests.post("https://api.upbit.com/v1/orders", headers=headers, json=params)
            if response.status_code in (200, 201):
                correct_flag = True
                break
        except:
            time.sleep(3)

    if not correct_flag:
        print(f"[RESPONSE] {response.text}")
        raise Exception("Failed to place buy order after 3 attempts.")

    result = response.json()
    print(f"[BUY SUCCESS] {market} | UUID: {result['uuid']}\n")
    return result

def buy_subject(not_have_subjects, access_key, secret_key):
    for subject in not_have_subjects:
        print(f"[BUY CHECKING] {subject} buy signal")
        
        is_subject_buy_signal = decide_buy(subject)
        if is_subject_buy_signal:
            print(f"[BUY CHECKING SUCCESS] {subject} buy signal")
            # 매수 로직
            available_volume = 10000
            
            buy_result = place_market_buy(access_key, secret_key, subject, available_volume)
            
            if buy_result:
                avg_price, volume = wait_buy_filled(access_key, secret_key, buy_result["uuid"])
            
            return subject, avg_price, volume
        else:
            print(f"[BUY CHECKING FAIL] {subject} no buy signal\n")
            
    return None, None, None
            
