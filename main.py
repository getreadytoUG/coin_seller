import requests
import jwt
import uuid
import os
import time

from dotenv import load_dotenv
from utils.decide import decide_buy, decide_buy_dummy
from utils.price import get_current_price
from trade import place_market_buy, decide_sell, place_market_sell

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

def get_balances(access_key, secret_key):
    payload = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get("https://api.upbit.com/v1/accounts", headers=headers)
    return res.json()


def check_subjects(access_key, secret_key, subject_list):
    balances = get_balances(access_key, secret_key)

    owned_markets = set()
    for b in balances:
        if float(b["balance"]) > 0:
            if b["currency"] != "KRW" and b["currency"] != "USDT":
                owned_markets.add(b["unit_currency"] + "-" + b["currency"])

    status = {s: (s in owned_markets) for s in subject_list}
    return status, balances

def get_available_balance(balances, currency):
    for b in balances:
        if b["currency"] == currency:
            return float(b["balance"])
    return 0.0

def count_available_slots(status_dict):
    return sum(1 for v in status_dict.values() if not v)


def calculate_buy_amount_per_market(
    balances,
    status_dict,
    quote_currency,
    min_order_amount
):
    available_balance = get_available_balance(balances, quote_currency)
    available_slots = count_available_slots(status_dict)

    if available_slots == 0:
        return 0.0

    amount_per_market = available_balance / available_slots

    if amount_per_market < min_order_amount:
        return 0.0
    return amount_per_market

def wait_buy_filled(access_key, secret_key, order_uuid, timeout=5):
    import time
    import requests
    import jwt
    import uuid as uuid_lib

    url = "https://api.upbit.com/v1/order"

    payload_base = {
        "access_key": access_key,
    }

    start = time.time()
    while time.time() - start < timeout:
        payload = {
            **payload_base,
            "nonce": str(uuid_lib.uuid4()),
            "uuid": order_uuid,
        }

        token = jwt.encode(payload, secret_key, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(url, headers=headers, params={"uuid": order_uuid})
        data = res.json()

        if data.get("state") == "done":
            avg_price = float(data["price"])
            volume = float(data["volume"])
            return avg_price, volume

        time.sleep(0.3)

    return None, None


if __name__ == "__main__":
    load_dotenv()
    
    access_key = os.getenv("ACCESS_KEY")
    secret_key = os.getenv("SECRET_KEY")
    
    subject_list = [
        "KRW-BTC",
        "KRW-ETH",
        "KRW-XRP",
        "KRW-SOL",
        "KRW-PLUME"
        # "KRW-ORCA"
        # "KRW-BARD",
        # "KRW-DOGE",
    ]
    
    while True:  
        # try:  
            status, balances = check_subjects(access_key, secret_key, subject_list)

            positions = init_positions_from_balances(balances, subject_list)
        # except Exception as e:
        #     print(f"[ERROR CODE 1] {e}")
        
        # try:
            for subject in subject_list:
                # 보유
                if status[subject]:
                    position = positions.get(subject)
                    if not position:
                        continue
                
                    current_price = get_current_price(subject)
                    
                    sell_signal = decide_sell(current_price, position)
                    
                    print(f"{subject} not ready to sell")
                    
                    if sell_signal:
                        print(f"[SELL READY] {subject}")
                        
                        result = place_market_sell(
                            access_key,
                            secret_key,
                            subject,
                            position["volume"]
                        )
                        
                        if result:
                            print(f"[SELL DONE] {subject}")
                            status[subject] = False
                            positions.pop(subject, None)
                    
                else:
                    # 미보유 → 매수 판단
                    if decide_buy(subject):
                    # if decide_buy_dummy(subject):
                        quote_currency = subject.split("-")[0]

                        min_order = 10 if quote_currency == "USDT" else 5000
                        
                        buy_amount = calculate_buy_amount_per_market(
                            balances=balances,
                            status_dict=status,
                            quote_currency=quote_currency,
                            min_order_amount=min_order
                        ) - 1

                        if buy_amount > 0:
                            print(f"[BUY READY] {subject} → {buy_amount:.2f} {quote_currency}")
                            # 실제 매수는 여기서
                            for i in range(3):
                                try:
                                    result = place_market_buy(access_key, secret_key, subject, buy_amount)
                                except:
                                    buy_amount -= 10

                            if result:
                                avg_price, volume = wait_buy_filled(access_key, secret_key, result["uuid"])
                                if avg_price:
                                    positions[subject] = {
                                        "init_price": avg_price,
                                        "max_price": avg_price,
                                        "volume": volume,
                                    }
                                    status[subject] = True
                                
            time.sleep(5)
        # except Exception as e:
        #     print(e)
        #     time.sleep(5)