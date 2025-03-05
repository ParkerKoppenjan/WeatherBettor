import time
import datetime
import utils.weather as weather
import utils.discord as discord
from utils.kalshi import Market
import settings

print("Weather Bettor v0.1")
print("Created by: @elliotjarnit and @ParkerKoppenjan")
print("Starting at " + str(datetime.datetime.now()))
print("Selected market: " + settings.SELECTED_MARKET + "\n")





# Set up the market to bet on (Los Angeles at this time, will be expanded)
market = Market(settings.SELECTED_MARKET)

# Get the forecasted high temperature for selected location(s)
forecasted_high = weather.get_forecasted_highest_temperature(settings.SELECTED_MARKET)

# Update forecasted high if current temperature is higher
current_temp = weather.get_current_temp(settings.SELECTED_MARKET)
if current_temp > forecasted_high:
    forecasted_high = current_temp
print("Forecasted high: " + str(forecasted_high))
# Makes initial bet based on forecasted high
range = market.get_range_for_temp(forecasted_high)
market.make_bet(range, settings.MAX_BET)

running = True
last_bet_price = market.get_bets()[-1].get_price()
last_temp = current_temp

def loop():
    """
     Main betting loop, runs once per minute, updates bets based on current temperature and market conditions.
    """
    global running
    global last_bet_price
    global last_temp

    market.update_prices()
    bets = market.get_bets()
    current_range = bets[-1].get_range()
    current_temp = weather.get_current_temp(settings.SELECTED_MARKET)
    current_price = current_range.get_price() #  so we don't have to call this every time

    if current_temp != last_temp:
        discord.send_webhook("Temperature Change", f"Temperature changed to {current_temp}°F")
        last_temp = current_temp

    # If high is reached before 11am, move to the next range
    if datetime.datetime.now().hour < 11 and current_temp == current_range.get_high():
        market.sell_all_bets()
        range_to_bet = market.get_range_for_temp(current_temp + 1)
        market.make_bet(range_to_bet, settings.MAX_BET)
        last_bet_price = market.get_bets()[-1].get_price()

    # If the current temp is higher than the current range, sell all bets and make a bet in the new range
    if current_temp > current_range.get_high():
        range_to_bet = market.get_range_for_temp(current_temp)
        market.sell_all_bets()
        market.make_bet(range_to_bet, settings.MAX_BET)
        last_bet_price = market.get_bets()[-1].get_price()

    # If the current price is higher than 0.95, sell all bets and stop the loop
    if current_price > 0.95:
        market.sell_all_bets()
        running = False

    # If the current price drops by 0.1, buy another bet
    if current_price < last_bet_price - 0.1:
        market.make_bet(current_range, settings.MAX_BET)
        last_bet_price = current_price


current_minute = time.localtime().tm_min
while running:
    # Run loop right when the minute changes
    if time.localtime().tm_min != current_minute:
        print(f"{settings.SELECTED_MARKET} - {time.strftime('%H:%M:%S', time.localtime())}")
        loop()
        print()

    # Check forecast every 5 minutes
    if current_minute % 5 == 0 and time.localtime().tm_min != current_minute:
        new_forecasted_high = weather.get_forecasted_highest_temperature(settings.SELECTED_MARKET)
        current_temp = weather.get_current_temp(settings.SELECTED_MARKET)
        if current_temp > new_forecasted_high:
            new_forecasted_high = current_temp

        range = market.get_range_for_temp(new_forecasted_high)
        if new_forecasted_high != forecasted_high and range.get_high() != market.get_bets()[0].get_range().get_high():
            print("Forecasted high changed to " + str(new_forecasted_high))
            forecasted_high = new_forecasted_high
            market.sell_all_bets()
            market.make_bet(range, settings.MAX_BET)
            last_bet_price = market.get_bets()[-1].get_price

    current_minute = time.localtime().tm_min
    time.sleep(0.5)











