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
print("Forecasted high: " + str(temp_high))
# makes initial bet based on forecasted high
range = market.get_range_for_temp(temp_high)
market.make_bet(range, settings.MAX_BET)

while running:
    market.update_prices()
    current_bet = market.get_current_bet()
    current_range = current_bet.get_range()
    current_temp = weather.get_current_temp(selected_market)
    if current_temp > current_range.get_high():
        range_to_bet = market.get_range_for_temp(current_temp)
        market.make_bet(range, settings.MAX_BET)

    percent_profit = current_range.get_price() - current_bet.get_price() # this works because shares add to 100 cents
    # Take profit
    if percent_profit > 0.25: # 25% profit
        market.sell_bet(current_bet)
        running = False
    # Stop loss
    elif percent_profit < -0.50: # 50% loss
        market.sell_bet(current_bet)
        running = False

    cooldown()










