import time
import weather
from kalshi import Market
import settings

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

running = True
last_bet_price = market.get_bets()[0].get_price()

def loop():
    global running
    global last_bet_price

    market.update_prices()
    bets = market.get_bets()
    current_range = bets[0].get_range()
    current_temp = weather.get_current_temp(selected_market)

    # If the current temp is higher than the current range, sell all bets and make a bet in the new range
    if current_temp > current_range.get_high():
        range_to_bet = market.get_range_for_temp(current_temp)
        market.sell_all_bets()
        market.make_bet(range, settings.MAX_BET)
        last_bet_price = market.get_bets()[0].get_price()

    # If the current price is higher than 0.95, sell all bets and stop the loop
    if current_range.get_price() > 0.95:
        market.sell_all_bets()
        running = False

    # If the current price drops by 0.1, buy another bet
    if current_range.get_price() < last_bet_price - 0.1:
        market.make_bet(current_range, settings.MAX_BET)
        last_bet_price = current_range.get_price()


# Run loop right when the minute changes
current_minute = time.localtime().tm_min
while running:
    if time.localtime().tm_min != current_minute:
        loop()
        current_minute = time.localtime().tm_min
        time.sleep(0.2)











