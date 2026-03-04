import requests
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

def get_balances(access_key, secret_key):
    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, secret_key)
    headers = {
        'Authorization': f'Bearer {jwt_token}'
    }

    response = requests.get("https://api.upbit.com/v1/accounts", headers=headers)
    return response.json()

def market_to_currency(market: str) -> str:
    # "KRW-BTC" → "BTC"
    return market.split("-")[1]

def check_current_status(balances, markets):
    """
    balances: 업비트 accounts API 결과
    markets: ["USDT-BTC", "KRW-ETH", ...]
    
    return:
    {
        "USDT-BTC": True/False,
        "KRW-ETH": True/False,
        ...
    }
    """

    # 현재 보유 중인 코인 심볼 집합
    owned_currencies = {
        b["currency"]
        for b in balances
        if float(b["balance"]) > 0
    }

    status = {}

    for market in markets:
        currency = market_to_currency(market)
        status[market] = currency in owned_currencies

    return status


def check_subjects(access_key, secret_key, markets):
    markets = ["USDT-BTC", "KRW-ETH", "BTC-SOL", "KRW-XRP", "KRW-DOGE"]    

    balances = get_balances(access_key, secret_key)
    status = check_current_status(balances, markets)
    
    for market, has_coin in status.items():
        print(f"{market}: {'보유중' if has_coin else '미보유'}")
        
    return status, balances


def check_available_balance(balances, currency):
    for b in balances:
        if b["currency"] == currency:
            return float(b["balance"])
    return 0.0