import jwt
import uuid
import requests
import hashlib
from urllib.parse import unquote, urlencode

from apis import get_current_price, get_candles

def extract_closes(candles):
    """
    종가 뽑는 함수
    """
    closes = [c["trade_price"] for c in candles]
    return closes[::-1] # 과거 -> 현재 순서대로 정렬

def check_high_break_or_near(candles, lookback=20, near_ratio=0.995):
    if len(candles) < lookback + 1:
        return False
    
    highs = [c["high_price"] for c in candles[1:lookback+1]]
    prev_high = max(highs)
    current_price = candles[0]["trade_price"]
    
    breakout = current_price > prev_high
    near = current_price >= prev_high * near_ratio
    
    return breakout or near

def calculate_ema(prices, period):
    """
    prices: 과거 -> 현재 순서
    period: EMA 기간 (20, 60 등)
    """
    if len(prices) < period:
        raise ValueError

    k = 2 / (period + 1)
    ema = prices[0]

    for price in prices[1:]:
        ema = price * k + ema * (1 - k)

    return ema

def calculate_ema_diff(candles, short_period=20, long_period=60):
    """
    candles: 업비트 캔들 리스트 (1분봉 or 5분봉)
    return: ema20 - ema60
    """
    closes = extract_closes(candles)

    # EMA 안정화를 위해 충분히 사용
    stable_closes = closes[-200:]

    ema_short = calculate_ema(stable_closes, short_period) # ema20 여기서 확인 가능
    ema_long = calculate_ema(stable_closes, long_period)

    return ema_short - ema_long, ema_short

def is_volume_increasing(candles, lookback=20, multiplier=1.3):
    if len(candles) < lookback + 1:
        return False

    current = candles[0]
    current_volume = current["candle_acc_trade_volume"]
    avg_volume = sum(
        c["candle_acc_trade_volume"] for c in candles[1:lookback+1]
    ) / lookback
    
    volume_increase = current_volume > avg_volume * multiplier
    bullish = current["trade_price"] > current["opening_price"]
    
    return volume_increase and bullish


def ema_diff_can_buy(market):
    # 1분봉 계산
    candles_1m = get_candles(1, market)
    ema_diff_1m, ema_20 = calculate_ema_diff(candles_1m)

    if ema_diff_1m < 0:
        return False, ema_20

    # 5분봉 계산
    candles_5m = get_candles(5, market)
    ema_diff_5m, _ = calculate_ema_diff(candles_5m)

    if ema_diff_5m < 0:
        return False, ema_20
    
    # 1분봉 거래량 계산
    if not is_volume_increasing(candles_1m):
        return False, ema_20
    
    # 고점 근처
    if not check_high_break_or_near(candles_1m):
        return False, ema_20
    
    return True, ema_20


def init_positions_from_balances(balances, subject_list):
    positions = {}

    for b in balances:
        market = b["unit_currency"] + "-" + b["currency"]
        if market in subject_list and float(b["balance"]) > 0:
            positions[market] = {
                "init_price": float(b["avg_buy_price"]),
                "max_price": float(b["avg_buy_price"]),
                "volume": float(b["balance"]),
            }

    return positions


def check_subjects(subject_list, balances):
    owned_markets = set()
    for b in balances:
        if float(b["balance"]) > 0:
            if b["currency"] != "KRW" and b["currency"] != "USDT":
                owned_markets.add(b["unit_currency"] + "-" + b["currency"])

    status = {s: (s in owned_markets) for s in subject_list}
    return status

def have_enough_balance(balances):
    for b in balances:
        if b["currency"] == "KRW":
            if float(b["balance"]) < 10000:  # 수수료 고려
                return False
    return True

def decide_sell(current_price, init_price):
    # 매도 조건: 현재 가격이 초기 가격보다 3% 이상 상승한 경우
    print(f"[INIT PRICE] {init_price} | [CURRENT PRICE] {current_price}")
    if (current_price >= init_price * 1.03) or (current_price <= init_price * 0.995):
        return True
    return False


def decide_buy(subject):
    can_buy_subject, ema_20_subject = ema_diff_can_buy(subject)
    
    if not can_buy_subject:
        return False
    
    current_price = get_current_price(subject)
    
    if current_price < ema_20_subject:
        return False
    
    return True


def make_jwt_token(access_key, secret_key, params):    
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