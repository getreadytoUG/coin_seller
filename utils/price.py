import json
import time
import requests

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

if __name__ == "__main__":
    print(get_current_price("KRW-BARD"))