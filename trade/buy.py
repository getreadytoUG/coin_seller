import time

import requests
import jwt
import uuid
from urllib.parse import unquote, urlencode
import hashlib


UPBIT_ORDER_URL = "https://api.upbit.com/v1/orders"

def place_market_buy(access_key, secret_key, market, price):
    """
    market: 예) 'KRW-BTC', 'USDT-BTC'
    price: 사용 금액 (KRW or USDT)
    """
    
    def make_jwt_token():
        params = {
            "market": market,
            "side": "bid",
            "ord_type": "price",
            "price": price,
        }
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
            time.sleep(1)

    if not correct_flag:
        print(f"[RESPONSE] {response.text}")
        raise Exception("Failed to place buy order after 3 attempts.")

    result = response.json()
    print(f"[BUY SUCCESS] {market} | UUID: {result['uuid']}")
    return result