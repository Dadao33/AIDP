"""Daily scenario allocation of the learned seven-day total, not a new ML model."""
from datetime import date, timedelta
import math

def daily_forecast(case, total, promo):
    weights=[a*(1+promo*b) for a,b in zip(case['daily_profile'],case['promotion_daily_weights'])]
    raw=[total*w/sum(weights) for w in weights]
    units=[math.floor(x) for x in raw]
    order=sorted(range(7),key=lambda i:(-(raw[i]-units[i]),i))
    for i in order[:total-sum(units)]:units[i]+=1
    return [dict(date=(date(2026,8,25)+timedelta(days=i)).isoformat(),units=units[i]) for i in range(7)]
