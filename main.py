from dotenv import load_dotenv
import os
import time

from apis import get_balances, sell_subject, buy_subject
from utils import init_positions_from_balances, check_subjects, have_enough_balance

load_dotenv()
access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")
subject_list = os.getenv("MARKET_LIST").split(", ")

if __name__ == "__main__":
    balances = get_balances(access_key, secret_key)
    positions = init_positions_from_balances(balances, subject_list)

    already_have_subjects = [k for k in positions.keys()]
    not_have_subjects = [s for s in subject_list if s not in already_have_subjects]
    
    time.sleep(5)
    while True:
        balances = get_balances(access_key, secret_key)
        status = check_subjects(subject_list, balances)
        
        enough_balance = have_enough_balance(balances)
        if enough_balance:
            # 매수 로직
            new_buy_subject, avg_price, volume = buy_subject(not_have_subjects, access_key, secret_key)
            if new_buy_subject:
                already_have_subjects.append(new_buy_subject)
                not_have_subjects.remove(new_buy_subject)

                positions[new_buy_subject] = {
                    "init_price": avg_price,
                    "max_price": avg_price,
                    "volume": volume,
                }
            
            # 매도 로직
            new_sell_subject = sell_subject(positions, access_key, secret_key)
            if new_sell_subject:
                already_have_subjects.remove(new_sell_subject)
                not_have_subjects.append(new_sell_subject)
                positions.pop(new_sell_subject, None)
        else:
            # 매도 로직
            new_sell_subject = sell_subject(positions, access_key, secret_key)
            if new_sell_subject:
                already_have_subjects.remove(new_sell_subject)
                not_have_subjects.append(new_sell_subject)
                positions.pop(new_sell_subject, None)

        time.sleep(5)