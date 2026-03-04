import requests
import jwt
import uuid

UPBIT_ORDER_URL = "https://api.upbit.com/v1/orders"


def place_market_buy(access_key, secret_key, market, price):
    """
    market: 예) 'KRW-BTC', 'USDT-BTC'
    price: 사용 금액 (KRW or USDT)
    """

    payload = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, secret_key, algorithm="HS256")
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    data = {
        "market": market,
        "side": "bid",
        "ord_type": "price",   # 시장가 매수
        "price": str(round(price, 2))  # 소수점 방어
    }

    response = requests.post(UPBIT_ORDER_URL, headers=headers, json=data)

    if response.status_code != 201:
        print(f"[BUY FAIL] {market}")
        print(response.status_code, response.text)
        return None

    result = response.json()
    print(f"[BUY SUCCESS] {market} | UUID: {result['uuid']}")
    return result