import json

import jwt
import uuid
import requests
import time
import uuid as uuid_lib
import hashlib
from urllib.parse import urlencode

def get_balances(access_key, secret_key):
    payload = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    headers = {"Authorization": f"Bearer {token}"}
    
    correct_flag = False
    for _ in range(3):
        try:
            res = requests.get("https://api.upbit.com/v1/accounts", headers=headers)
            if res.status_code in (200, 201):
                correct_flag = True
                break
            break
        except:
            time.sleep(3)
    
    if not correct_flag:
        print(f"[RESPONSE] {res.text}")
        raise Exception("Failed to fetch balances after 3 attempts.")
            
    return res.json()


def get_current_price(subject):
    url = "https://api.upbit.com/v1/ticker"

    params = {"markets": subject}

    headers = {"accept": "application/json"}

    correct_flag = False
    for _ in range(3):
        try:
            response = requests.get(url, headers=headers, params=params)
            current_price = json.loads(response.text)[0]["trade_price"]
            
            correct_flag = True
            break
        except:
            time.sleep(3)
    
    if not correct_flag:
        print(f"[RESPONSE] {response.text}")
        raise Exception(f"Failed to fetch current price for {subject} after 3 attempts.")
    
    return current_price

def get_candles(unit, market):
    url = f"https://api.upbit.com/v1/candles/minutes/{unit}"

    # params = {"market": "USDT-BTC", "count": 200}
    params = {"market": market, "count": 200}

    headers = {"accept": "application/json"}

    correct_flag = False
    for _ in range(3):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code in (200, 201):
                correct_flag = True
                break
        except:
            time.sleep(3)
            
    if not correct_flag:
        print(f"[RESPONSE] {response.text}")
        raise Exception("Failed to fetch candles after 3 attempts.")

    candles = json.loads(response.text)

    return candles



def wait_buy_filled(access_key, secret_key, order_uuid, timeout=5):
    url = "https://api.upbit.com/v1/order"

    start = time.time()
    while time.time() - start < timeout:
        params = {"uuid": order_uuid}
        
        # query hash 생성
        query_string = urlencode(params).encode()
        query_hash = hashlib.sha512(query_string).hexdigest()
        
        payload = {
            "access_key": access_key,
            "nonce": str(uuid_lib.uuid4()),
            "query_hash": query_hash,
            "query_hash_alg": "SHA512",
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(url, headers=headers, params=params)
        data = res.json()

        if data.get("state") in ("done", "cancel"):
            executed = float(data.get("executed_volume", 0))
            if executed > 0:
                avg_price = float(data["trades"][0]["price"])
                # 또는 체결금액/체결수량
                volume = executed
                return avg_price, volume

        time.sleep(0.3)
        
    return None, None