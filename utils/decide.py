from utils.candle import ema_diff_can_buy
from utils.price import get_current_price

def decide_buy(subject):
    can_buy_subject, ema_20_subject = ema_diff_can_buy(subject)
    
    if not can_buy_subject:
        return False
    
    current_price = get_current_price(subject)
    
    if current_price < ema_20_subject:
        print(f"{subject} Flase 5")
        return False
    
    print(f"{subject} True")
    return True
    
    
    
def decide_buy_dummy(subject):
    return True