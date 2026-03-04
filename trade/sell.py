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
        "max_price": float,
        "volume": float
    }
    """

    init_price = position["init_price"]
    max_price = position["max_price"]

    # 최고가 갱신
    if current_price > max_price:
        position["max_price"] = current_price
        return False  # 아직 안 판다

    gain_from_entry = (max_price - init_price) / init_price * 100
    drawdown_from_max = (current_price - max_price) / max_price * 100

    # 1️⃣ +3% 미만 → -3% 손절
    if gain_from_entry < 3:
        if (current_price - init_price) / init_price * 100 <= -3:
            return True

    # 2️⃣ +3% 이상 +6% 미만 → 본전 청산
    elif gain_from_entry < 6:
        if current_price <= init_price:
            return True

    # 3️⃣ +6% 이상 → 최고가 대비 -6%
    else:
        if drawdown_from_max <= -6:
            return True

    return False


def place_market_sell(access_key, secret_key, market, volume):
    params = {
        "market": market,
        "side": "ask",
        "ord_type": "market",
        "volume": volume
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
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/json"
    }

    response = requests.post(UPBIT_ORDER_URL, headers=headers, json=params)

    if response.status_code != 201:
        print(f"[SELL FAIL] {market}")
        print(response.status_code, response.text)
        return None

    result = response.json()
    print(f"[SELL SUCCESS] {market} | UUID: {result['uuid']}")
    return result