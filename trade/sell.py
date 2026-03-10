import time

import jwt
import uuid
import requests
from urllib.parse import unquote, urlencode
import hashlib

UPBIT_ORDER_URL = "https://api.upbit.com/v1/orders"

def decide_sell(current_price, position):
    """
    position = {
        "init_price": float,
        "volume": float
    }
    """

    init_price = position["init_price"]
    change = (current_price - init_price) / init_price * 100

    # -1.5% 손절 또는 +5% 익절
    if change <= -1.5 or change >= 5:
        return True

    return False


def place_market_sell(access_key, secret_key, market, volume):
    params = {
        "market": market,
        "side": "ask",
        "ord_type": "market",
        "volume": volume
    }
    
    def make_jwt_token():
        query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
        
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            "access_key": access_key,
            "nonce": str(uuid.uuid4()),
            "query_hash": query_hash,
            "query_hash_alg": "SHA512"
        }

        jwt_token = jwt.encode(payload, secret_key, algorithm="HS256")
        return jwt_token, params
    
    correct_flag = False
    for _ in range(3):
        try:
            jwt_token, params = make_jwt_token()
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/json"
            }
            response = requests.post(UPBIT_ORDER_URL, headers=headers, json=params)
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