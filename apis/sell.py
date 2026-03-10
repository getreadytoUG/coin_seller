import time
import requests

from utils import decide_sell, make_jwt_token
from apis import get_current_price


def sell_subject(positions, access_key, secret_key):
    for subject, position in positions.items():
        print(f"[SELL CHECKING] {subject} sell signal")
        
        current_price = get_current_price(subject)
        
        sell_signal = decide_sell(current_price, position["init_price"])
        
        if sell_signal:
            print(f"[SELL CHECKING SUCCESS] {subject} sell signal")
            
            result = place_market_sell(
                access_key,
                secret_key,
                subject,
                position["volume"]
            )
            
            if result:
                print(f"[SELL DONE] {subject}")
                return subject
        else:
            print(f"[SELL CHECKING FAIL] {subject} no sell signal\n")
    return None
        


def place_market_sell(access_key, secret_key, market, volume):
    params = {
        "market": market,
        "side": "ask",
        "ord_type": "market",
        "volume": volume
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
        raise Exception("Failed to place sell order after 3 attempts.")

    result = response.json()
    print(f"[SELL SUCCESS] {market} | UUID: {result['uuid']}")
    return result