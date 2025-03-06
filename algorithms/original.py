from algorithms import Algorithm
from utils import discord, weather
import datetime
import settings

class OriginalAlgorithm(Algorithm):
    NAME = "Original Algorithm"
    VERSION = "0.1 BETA"
    LOOP_INTERVAL = 60

    def __init__(self):
        self.last_bet_price = None
        self.last_temp = 0

    def init(self, market):
        # Get the forecasted high temperature for selected location(s)
        forecasted_high = weather.get_forecasted_highest_temperature(market.city)

        # Update forecasted high if current temperature is higher
        current_temp = weather.get_current_temp(market.city)
        if current_temp > forecasted_high:
            forecasted_high = current_temp
        print("Forecasted high: " + str(forecasted_high))

        # Makes initial bet based on forecasted high
        range = market.get_range_for_temp(forecasted_high)
        market.make_bet(range, settings.MAX_BET)

        self.last_bet_price = market.get_bets()[-1].get_price()
        self.last_temp = current_temp

    def loop(self, market):
        market.update_prices()
        bets = market.get_bets()
        current_range = bets[-1].get_range()
        current_temp = weather.get_current_temp(market.city)
        current_price = current_range.get_price() #  so we don't have to call this every time

        if current_temp != self.last_temp:
            discord.send_webhook("Temperature Change", f"Temperature changed to {current_temp}°F")
            self.last_temp = current_temp

        # If high is reached before 11am, move to the next range
        if datetime.datetime.now().hour < 11 and current_temp == current_range.get_high():
            market.sell_all_bets()
            range_to_bet = market.get_range_for_temp(current_temp + 1)
            market.make_bet(range_to_bet, settings.MAX_BET)
            self.last_bet_price = market.get_bets()[-1].get_price()

        # If the current temp is higher than the current range, sell all bets and make a bet in the new range
        if current_temp > current_range.get_high():
            range_to_bet = market.get_range_for_temp(current_temp)
            market.sell_all_bets()
            market.make_bet(range_to_bet, settings.MAX_BET)
            self.last_bet_price = market.get_bets()[-1].get_price()

        # If the current price is higher than 0.95, sell all bets and stop the loop
        if current_price > 0.95:
            market.sell_all_bets()
            self.stop()

        # If the current price drops by 0.1, buy another bet
        if current_price < self.last_bet_price - 0.1:
            market.make_bet(current_range, settings.MAX_BET)
            self.last_bet_price = current_price