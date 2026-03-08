"""
첫번째 조건인 ema20_1 > ema60_1 and ema20_5 > ema60_5 조건 보기
"""
import time

import requests
import json

def check_high_break_or_near(candles, lookback=20, near_ratio=0.995):
    if len(candles) < lookback + 1:
        return False
    
    highs = [c["high_price"] for c in candles[1:lookback+1]]
    prev_high = max(highs)
    current_price = candles[0]["trade_price"]
    
    breakout = current_price > prev_high
    near = current_price >= prev_high * near_ratio
    
    return breakout or near


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
            time.sleep(1)
            
    if not correct_flag:
        print(f"[RESPONSE] {response.text}")
        raise Exception("Failed to fetch candles after 3 attempts.")

    candles = json.loads(response.text)

    return candles

def extract_closes(candles):
    """
    종가 뽑는 함수
    """
    closes = [c["trade_price"] for c in candles]
    return closes[::-1] # 과거 -> 현재 순서대로 정렬

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

def ema_diff_can_buy(market):
    # 1분봉 계산
    candles_1m = get_candles(1, market)
    ema_diff_1m, ema_20 = calculate_ema_diff(candles_1m)

    if ema_diff_1m < 0:
        print(f"{market} False 1 : EMA Difference 1minute")
        return False, ema_20

    # 5분봉 계산
    candles_5m = get_candles(5, market)
    ema_diff_5m, _ = calculate_ema_diff(candles_5m)

    if ema_diff_5m < 0:
        print(f"{market} False 2 : EMA Difference 5minute")
        return False, ema_20
    
    # 1분봉 거래량 계산
    if not is_volume_increasing(candles_1m):
        print(f"{market} False 3 : Not enough amount")
        return False, ema_20
    
    # 고점 근처
    if not check_high_break_or_near(candles_1m):
        print(f"{market} False 4 : Not near the highest")
        return False, ema_20
    
    return True, ema_20


if __name__ == "__main__":
    can_buy_btc, ema_20_btc = ema_diff_can_buy("USDT-BTC")
    can_buy_eth, ema_20_eth = ema_diff_can_buy("KRW-ETH")
    can_buy_sol, ema_20_sol = ema_diff_can_buy("BTC-SOL")
    can_buy_xrp, ema_20_xrp = ema_diff_can_buy("KRW-XRP")
    can_buy_doge, ema_20_doge = ema_diff_can_buy("KRW-DOGE")
    
    
    print(can_buy_btc, ema_20_btc)
    print(can_buy_eth, ema_20_eth)
    print(can_buy_sol, ema_20_sol)
    print(can_buy_xrp, ema_20_xrp)
    print(can_buy_doge, ema_20_doge)