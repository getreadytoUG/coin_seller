import json
import requests

def get_current_price(subject):
    url = "https://api.upbit.com/v1/ticker"

    params = {"markets": subject}

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers, params=params)
    
    current_price = json.loads(response.text)[0]["trade_price"]
    
    return current_price

if __name__ == "__main__":
    print(get_current_price("KRW-BARD"))