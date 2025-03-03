import time
import weather
from kalshi import Market
import settings

selected_market = "LA"
market = Market(selected_market)

running = True
last_bet_price = market.get_bets()[0].get_price()
forecasted_high = weather.get_forecasted_highest_temperature(selected_market)

current_temp = weather.get_current_temp(selected_market)
if current_temp > forecasted_high:
    forecasted_high = current_temp
print("Forecasted high: " + str(forecasted_high))
# makes initial bet based on forecasted high
range = market.get_range_for_temp(forecasted_high)
market.make_bet(range, settings.MAX_BET)

def loop():
    global running
    global last_bet_price

    market.update_prices()
    bets = market.get_bets()
    current_range = bets[-1].get_range()
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


current_minute = time.localtime().tm_min
while running:
    print(f"{selected_market} - {time.localtime().tm_hour}:{time.localtime().tm_min}")
    # Run loop right when the minute changes
    if time.localtime().tm_min != current_minute:
        loop()
        current_minute = time.localtime().tm_min

    # Check forecast every 5 minutes
    if current_minute % 5 == 0:
        new_forecasted_high = weather.get_forecasted_highest_temperature(selected_market)
        current_temp = weather.get_current_temp(selected_market)
        if current_temp > new_forecasted_high:
            new_forecasted_high = current_temp

        range = market.get_range_for_temp(new_forecasted_high)
        if new_forecasted_high != forecasted_high and range.get_high() != market.get_bets()[0].get_range().get_high():
            print("Forecasted high changed to " + str(new_forecasted_high))
            forecasted_high = new_forecasted_high
            market.sell_all_bets()
            market.make_bet(range, settings.MAX_BET)
            last_bet_price = market.get_bets()[0].get_price

    print()
    time.sleep(0.2)











