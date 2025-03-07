from algorithms import Algorithm
from utils import discord, weather
import settings

class GuaranteedNoAlgorithm(Algorithm):
    NAME = "Guaranteed No Algorithm"
    VERSION = "0.1"
    LOOP_INTERVAL = 60

    def __init__(self):
        self.last_bet_price = None
        self.available_ranges = None
        self.max_temp = None  # Highest temp seen thus far (irrespective of forecasts)
        self.last_temp = 0

    def init(self, market):
        self.available_ranges = market.get_ranges()
        self.last_temp = weather.get_current_temp(market.city)

    def loop(self, market):
        market.update_prices()
        bets = market.get_bets()
        current_betting_range = None if not bets else bets[-1].get_range()
        current_temp = weather.get_current_temp(market.city)

        # Update max temperature
        if self.max_temp is None or current_temp > self.max_temp:
            self.max_temp = current_temp

        if current_temp != self.last_temp:
            discord.send_webhook("Temperature Change", f"Temperature changed to {current_temp}°F")
            self.last_temp = current_temp

        if not current_betting_range:  # If there are no bets, see if we can make one
            potential_ranges = []
            for r in self.available_ranges:
                if self.max_temp > r.get_high():  # If the high of a range has already been exceeded
                    potential_ranges.append(r)

            if potential_ranges:  # Check if we have any viable ranges
                cheapest_range = potential_ranges[0]
                for r in potential_ranges:
                    if r.get_price() < cheapest_range.get_price():  # Get cheapest range
                        cheapest_range = r

                if cheapest_range.get_price() < 0.95:  # Makes sure price is low enough to make any money
                    discord.send_webhook(f"Market Lag Spotted at Range {str(cheapest_range)}", "Swooping in for easy money...")
                    if market.make_bet(cheapest_range, settings.MAX_BET, False): # confirms the bet goes through properly
                        current_betting_range = cheapest_range
                        self.last_bet_price = market.get_bets()[-1].get_price()
        else:
            if current_betting_range.get_price() > 0.99: # Sell at 99 cents
                market.sell_all_bets(0.99)
                current_betting_range = None
            elif current_betting_range.get_price() < self.last_bet_price - 0.1: # If the price has dropped by at least 10 cents, make a new bet on the same range
                if market.make_bet(current_betting_range, settings.MAX_BET, False):
                    self.last_bet_price = current_betting_range.get_price()
