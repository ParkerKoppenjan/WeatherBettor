from algorithms import Algorithm
from utils import discord, weather
import settings

class GuaranteedNoAlgorithm(Algorithm):
    NAME = "Guaranteed No Algorithm"
    VERSION = "0.2"
    LOOP_INTERVAL = 60

    def __init__(self):
        self.last_bet_prices = {}
        self.available_ranges = None
        self.max_temp = None  # Highest temp seen thus far (irrespective of forecasts)
        self.last_temp = 0

    def init(self, market):
        self.available_ranges = market.get_ranges()
        self.last_temp = weather.get_current_temp(market.city)
        self.max_temp = self.last_temp

    def loop(self, market):
        market.update_prices()
        bets = market.get_bets()
        current_betting_ranges = [bet.get_range() for bet in bets] if bets else []
        current_temp = weather.get_current_temp(market.city, True)

        # Update max temperature
        if current_temp > self.max_temp:
            self.max_temp = current_temp

        if current_temp != self.last_temp:
            discord.send_webhook("Temperature Change", f"Temperature changed to {current_temp}°F")
            self.last_temp = current_temp

        potential_ranges = []
        for r in self.available_ranges:
            if r not in current_betting_ranges: # Confirming we don't already have a bet in that range
                if r.get_high() and self.max_temp > r.get_high():  # If the high of a range has already been exceeded
                    potential_ranges.append(r)

        if potential_ranges:  # Check if we have any viable ranges
            potential_ranges = sorted(potential_ranges, key=lambda x: x.get_no_price())
            for r in potential_ranges:
                if r.get_no_price() > 0.96:  # Makes sure price is low enough to make any money
                    break
                elif market.make_bet(r, settings.MAX_BET, False): # confirms the bet goes through properly
                    self.last_bet_prices[r] = r.get_no_price()
        else:
            if current_betting_ranges:
                for r in current_betting_ranges:
                    if r.get_no_price() > 0.99: # Sell at 99 cents
                        market.sell_bet(r)

                    elif r in self.last_bet_prices and r.get_no_price() < self.last_bet_prices[r] - 0.1: # If the price has dropped by at least 10 cents, make a new bet on the same range
                        if market.make_bet(r, settings.MAX_BET, False):
                            self.last_bet_prices[r] = r.get_no_price()

