import time
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
        market.make_bet(r, settings.MAX_BET)
        cooldown()
        break

while running:
    market.update_prices()
    if weather.get_current_temp(selected_market) > market.get_current_bet().range.high:
        market.make_bet(market.ranges[market.get_current_bet().range.high + 1], settings.MAX_BET)
        print("Made a new bet at " + str(market.get_current_bet().range.high + 1))

    percent_profit = market.get_current_bet().range.price - market.get_current_bet().price # this works because shares add to 100 cents
    # Take profit
    if percent_profit > 0.25: # 25% profit
        print("Sold bet at " + str(market.get_current_bet().range.high))
        market.sell_bet(market.get_current_bet())
        running = False
    # Stop loss
    elif percent_profit < -0.50: # 50% loss
        print("Sold bet at " + str(market.get_current_bet().range.high))
        market.sell_bet(market.get_current_bet())
        running = False
    cooldown()










