import time
import datetime
import weather
from kalshi import Market
import settings

def cooldown():
    time.sleep(settings.COOLDOWN)

running = True
selected_market = "LA"
market = Market(selected_market)
temp_high = weather.get_forecasted_highest_temperature(selected_market)
current_temp = weather.get_current_temp(selected_market)
if current_temp > temp_high:
    temp_high = current_temp
# makes initial bet based on forecasted high
for r in market.ranges:
    if r.number_in_range(temp_high):
        market.make_bet(r)
        cooldown()
        break

while running:
    market.update_prices()
    if weather.get_current_temp(selected_market) > market.get_current_bet().range.high:
        market.make_bet(market.ranges[market.get_current_bet().range.high + 1], settings.MAX_BET)

    percent_profit = market.get_current_bet.range.price - market.get_current_bet.price # this works because shares add to 100 cents
    if percent_profit > 0.25: # 25% profit
        market.sell_bet(market.get_current_bet())
        running = False
    elif percent_profit < -0.50: # 50% loss
        market.sell_bet(market.get_current_bet())
        running = False
    cooldown()










