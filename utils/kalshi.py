import json
import math
import time
import uuid
import discord

import requests
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from dotenv import load_dotenv
import os

load_dotenv()
private_key_name = os.environ["KALSHI_PRIVATE_KEY_NAME"]
access_key = os.environ["KALSHI_ACCESS_KEY"]

# Mapping of city names to their Kalshi tickers
tickers = {
    "AUSTIN": "kxhighaus",
    "NYC": "kxhighny",
    "DENVER": "kxhighden",
    "CHICAGO": "kxhighchi",
    "MIAMI": "kxhighmia",
    "LA": "kxhighlax",
    "PHILADELPHIA": "kxhighphil"
}

def load_private_key_from_file(file_path):
    """
    Load a private key from a PEM file.

    Args:
        file_path (str): Path to the private key file

    Returns:
        RSAPrivateKey: The loaded private key object
    """
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide a password if your key is encrypted
            backend=default_backend()
        )
    return private_key

def sign_pss_text(private_key, text):
    # Before signing, we need to hash our message.
    # The hash is what we actually sign.
    # Convert the text to bytes
    message = text.encode('utf-8')

    try:
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    except InvalidSignature as e:
        raise ValueError("RSA sign PSS failed") from e

private_key = load_private_key_from_file(private_key_name)

def make_signed_request_get(url):
    """
       Make a signed GET request to the Kalshi API.

       Args:
           url (str): The full URL to send the GET request to

       Returns:
           dict or str: The JSON response or text if not JSON
       """
    path = url.split("https://api.elections.kalshi.com")[1]
    current_time = datetime.now()
    timestamp = current_time.timestamp()
    current_time_milliseconds = int(timestamp * 1000)
    timestampt_str = str(current_time_milliseconds)
    msg_string = timestampt_str + "GET" + path
    sig = sign_pss_text(private_key, msg_string)
    headers = {
        'KALSHI-ACCESS-KEY': access_key,
        'KALSHI-ACCESS-SIGNATURE': sig,
        'KALSHI-ACCESS-TIMESTAMP': timestampt_str
    }
    response = requests.get(url, headers=headers)
    if not response.headers.get("Content-Type").startswith("application/json"):
        return response.text
    return response.json()

def make_signed_request_post(url, data):
    """
    Make a signed POST request to the Kalshi API.

    Args:
        url (str): The full URL to send the POST request to
        data (dict): The data to send in the POST request

    Returns:
        dict or str: The JSON response or text if not JSON
    """
    path = url.split("https://api.elections.kalshi.com")[1]
    current_time = datetime.now()
    timestamp = current_time.timestamp()
    current_time_milliseconds = int(timestamp * 1000)
    timestampt_str = str(current_time_milliseconds)
    msg_string = timestampt_str + "POST" + path
    sig = sign_pss_text(private_key, msg_string)
    headers = {
        'KALSHI-ACCESS-KEY': access_key,
        'KALSHI-ACCESS-SIGNATURE': sig,
        'KALSHI-ACCESS-TIMESTAMP': timestampt_str
    }
    response = requests.post(url, headers=headers, json=data)
    if not response.headers.get("Content-Type").startswith("application/json"):
        return response.text
    return response.json()

class Range:
    """
    Represents a temperature range on Kalshi that can be bet on.
    A range can have a low bound, high bound, or both.
    """
    def __init__(self, ticker, low, high, price, price_ask):
        """
        Initialize a new temperature range.

        Args:
            ticker (str): Kalshi ticker symbol for this range
            low (int or None): Lower bound of temperature range (None if no lower bound)
            high (int or None): Upper bound of temperature range (None if no upper bound)
            price (float): Current bid price for this range
            price_ask (float): Current ask price for this range
        """
        print(f"Creating range for {ticker} from {low} to {high} at {price} with ask price {price_ask}")
        self.ticker = ticker
        self.low = low
        self.high = high
        self.price = price
        self.price_ask = price_ask

    def __str__(self):
        if self.low is None and self.high is None:
            return "Any"
        elif self.low is None:
            return f"Up to {self.high}"
        elif self.high is None:
            return f"{self.low} and up"
        return f"{self.low} to {self.high}"

    def number_in_range(self, number):
        return (self.low is None or number >= self.low) and (self.high is None or number <= self.high)

    def get_high(self):
        return self.high

    def get_low(self):
        return self.low

    def get_price(self):
        return self.price

    def set_price(self, price):
        self.price = price

    def set_price_ask(self, price):
        self.price_ask = price

    def get_price_ask(self):
        return self.price_ask

    def get_ticker(self):
        return self.ticker

class Bet:
    """
      Represents a bet placed on Kalshi for a specific temperature range.
      Handles the creation and management of orders on the Kalshi platform.
    """
    def __init__(self, city, range, amount):
        """
        Initialize and place a new bet.

        Args:
            city (str): City being bet on
            range (Range): Temperature range being bet on
            amount (float): Maximum amount to bet in dollars
        """
        self.city = city
        self.range = range
        self.client_order_id = str(uuid.uuid4())
        self.price = max(range.get_price_ask(), 0.01)
        self.count = math.floor(amount / self.price)

        print(f"Making bet for {self.city} at {self.range} for {self.count} shares at {self.price}")

        url = f"https://api.elections.kalshi.com/trade-api/v2/portfolio/orders"

        data = {
            "action": "buy",
            "ticker": range.get_ticker(),
            "side": "yes",
            "type": "market",
            "client_order_id": self.client_order_id,
            "count": self.count,
            "yes_price": 0,
            "no_price": 0
        }

        response = make_signed_request_post(url, data)
        if response.get("error"):
            print("Something went wrong while placing bet")
            print(response.get("error"))
            discord.send_webhook("Error Placing Bet", f"Error placing bet for {self.city} at {self.range} for {self.count} shares at {self.price}")
            raise ValueError("Error placing bet")

        order = response.get("order")
        print("\nCurrent order status:")
        print(json.dumps(order, indent=2))
        print()
        try:
            self.status = order.get("status")
            self.id = order.get("order_id")
            while self.status == "resting" or self.status == "pending":
                time.sleep(1)
                url = f"https://api.elections.kalshi.com/trade-api/v2/portfolio/orders/{self.id}"
                response = make_signed_request_get(url)
                order = response.get("order")
                print("\nCurrent order status:")
                print(json.dumps(order, indent=2))
                print()
                self.status = order.get("status")

            print(f"Successfully placed bet for {self.city} at {self.range} for {self.count} shares at {self.price}")
            discord.send_webhook("Bet Placed", f"Bet placed for {self.city} at {self.range} for {self.count} shares at {self.price}")
        except:
            print("Error placing bet")
            print(response)
            discord.send_webhook("Error Placing Bet", f"Error placing bet for {self.city} at {self.range} for {self.count} shares at {self.price}")
            raise ValueError("Error placing bet")



    def check_status(self):
        """
        Check the current status of this bet on Kalshi.

        Returns:
            str: Current status of the order
        """
        url = f"https://api.elections.kalshi.com/trade-api/v2/portfolio/orders/{self.id}"
        response = make_signed_request_get(url)
        order = response.get("order")
        self.status = order.get("status")
        return self.status

    def __str__(self):
        return f"{self.city}: {self.range}"

    def pull_out(self):
        """
        Sell this bet and exit the position.

        Returns:
            dict: Order details from Kalshi
        """
        print(f"Pulling out of {self.city} at {self.range} for {self.count} shares")

        url = f"https://api.elections.kalshi.com/trade-api/v2/portfolio/orders"

        data = {
            "action": "sell",
            "client_order_id": str(uuid.uuid4()),
            "count": self.count,
            "yes_price": 0,
            "no_price": 0,
            "type": "market",
            "ticker": self.range.get_ticker(),
            "side": "yes"
        }

        response = make_signed_request_post(url, data)

        if response.get("error"):
            print("Something went wrong while pulling out")
            print(response.get("error"))
            discord.send_webhook("Error Selling Bet", f"Error selling bet for {self.city} at {self.range} for {self.count} shares at {self.price}")
            return None

        try:
            order = response.get("order")
            if order:
                print(f"Successfully pulled out of {self.city} at {self.range} for {self.count} shares at {order.get('yes_price')}")
                discord.send_webhook("Bet Sold", f"Bet sold for {self.city} at {self.range} for {self.count} shares at {order.get('yes_price')}")
                del self

            return order
        except:
            print("Error selling bet")
            print(response)
            discord.send_webhook("Error Selling Bet", f"Error selling bet for {self.city} at {self.range} for {self.count} shares at {self.price}")
            return None

    def get_range(self):
        return self.range

    def get_price(self):
        return self.price

    def get_potential_profit(self):
        return self.count * (self.range.get_price() - self.price)


class Market:
    """
    Represents a city's weather betting market on Kalshi.
    Manages the available temperature ranges and placed bets for a city.
    """
    valid_markets = ["AUSTIN", "NYC", "DENVER", "CHICAGO", "MIAMI", "LA", "PHILADELPHIA"]

    def __init__(self, city):
        """
        Initialize a market for a specific city.

        Args:
            city (str): City to track

        """
        if city not in Market.valid_markets:
            raise ValueError("Invalid city")
        self.city = city
        self.ranges = self.update_ranges()
        self.bets = []


    def update_ranges(self):
        """
        Update the available temperature ranges for this market from Kalshi.

        Returns:
            list: Updated list of Range objects
        """
        event = get_event_for_city(self.city)
        markets = event.get("markets")
        ranges = []

        for market in markets:
            name = market.get("yes_sub_title")
            degree_count = name.count('°')
            price = market.get("yes_bid") / 100
            price_ask = market.get("yes_ask") / 100

            if degree_count == 1:
                if name.count('above') > 0:
                    ranges.append(Range(market.get("ticker"), int(name.split('°')[0]), None, price, price_ask))
                else:
                    ranges.append(Range(market.get("ticker"), None, int(name.split('°')[0]), price, price_ask))
            else:
                range_split = name.split('to')
                range1 = int(range_split[0].split('°')[0])
                range2 = int(range_split[1].split('°')[0])
                ranges.append(Range(market.get("ticker"), range1, range2, price, price_ask))

        self.ranges = ranges
        return ranges

    def update_prices(self):
        """Update the prices for all temperature ranges from the current Kalshi market data."""

        event = get_event_for_city(self.city)
        markets = event.get("markets")

        for market in markets:
            ticker = market.get("ticker")
            price = market.get("yes_bid") / 100
            price_ask = market.get("yes_ask") / 100
            for r in self.ranges:
                if r.get_ticker() == ticker:
                    r.set_price(price)
                    r.set_price_ask(price_ask)

        for r in self.ranges:
            print(f"Range: {r} has price {r.get_price()} and ask price {r.get_price_ask()}")

    def get_bets(self):
        return self.bets

    def make_bet(self, range, amount):
        if len(self.bets) > 0:
            print("Warning: Already have a bet")

        if range.get_price() < 0.01 or range.get_price_ask() < 0.01:
            print("Warning: Price is too low")
            return None

        if range.get_price_ask() > 0.95:
            print("Warning: Price is too high")
            return None

        bet = None
        try :
            bet = Bet(self.city, range, amount)
        except:
            return None
        self.bets.append(bet)
        return bet

    def sell_bet(self, bet):
        try:
            bet.pull_out()
        except:
            return
        self.bets.remove(bet)

    def get_range_for_temp(self, temp):
        for r in self.ranges:
            if r.number_in_range(temp):
                return r
        return None

    def get_total_potential_profit(self):
        return sum([bet.get_potential_profit() for bet in self.bets])

    def sell_all_bets(self):
        for bet in self.bets:
            bet.pull_out()
        self.bets = []


def get_date_in_kalshi_format():
    return datetime.now().strftime('%y%b%d').upper()

def get_todays_weather_ticker(city):
    return tickers.get(city.upper()).upper() + '-' + get_date_in_kalshi_format()

def get_event_for_city(city):
    url = f"https://api.elections.kalshi.com/trade-api/v2/events/{get_todays_weather_ticker(city)}"
    response = make_signed_request_get(url)
    if not isinstance(response, dict) or response.get("error") or not response.get("event"):
        print("Incorrect response from Kalshi")
        print(response)
        return {
            "event": {}
        }
    return response