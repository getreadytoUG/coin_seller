import jwt
import uuid
import requests

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


def place_market_sell(access_key, secret_key, subject, volume):
    url = "https://api.upbit.com/v1/orders"

    query = {
        "market": subject,      # 예: KRW-BTC
        "side": "ask",           # 매도
        "volume": str(volume),   # 매도 수량
        "ord_type": "market",    # 시장가
    }

    payload = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    res = requests.post(url, json=query, headers=headers)

    if res.status_code != 201:
        print("[SELL ERROR]", res.text)
        return None

    return res.json()