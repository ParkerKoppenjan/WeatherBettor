import math
import uuid

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
    return response.json()

def make_signed_request_post(url, data):
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
    return response.json()

class Range:
    def __init__(self, ticker, low, high, price, price_ask):
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
    def __init__(self, city, range, amount):
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
        order = response.get("order")
        if order:
            print(f"Successfully placed bet for {self.city} at {self.range} for {self.count} shares at {order.get('yes_price')}")
        self.id = order.get("order_id")
        self.status = order.get("status")

    def check_status(self):
        url = f"https://api.elections.kalshi.com/trade-api/v2/portfolio/orders/{self.id}"
        response = make_signed_request_get(url)
        order = response.get("order")
        self.status = order.get("status")
        return self.status

    def __str__(self):
        return f"{self.city}: {self.range}"

    def pull_out(self):
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

        order = response.get("order")
        if order:
            print(f"Successfully pulled out of {self.city} at {self.range} for {self.count} shares at {order.get('yes_price')}")
            del self

        return order

    def get_range(self):
        return self.range

    def get_price(self):
        return self.price


class Market:
    valid_markets = ["AUSTIN", "NYC", "DENVER", "CHICAGO", "MIAMI", "LA", "PHILADELPHIA"]

    def __init__(self, city):
        if city not in Market.valid_markets:
            raise ValueError("Invalid city")
        self.city = city
        self.ranges = self.update_ranges()
        self.bet = None

    def update_ranges(self):
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

    def get_current_bet(self):
        return self.bet

    def make_bet(self, range, amount):
        if self.bet:
            self.bet.pull_out()

        bet = Bet(self.city, range, amount)
        self.bet = bet
        return bet

    def sell_bet(self, bet):
        bet.pull_out()
        self.bet = None

    def get_range_for_temp(self, temp):
        for r in self.ranges:
            if r.number_in_range(temp):
                return r
        return None


def get_date_in_kalshi_format():
    return datetime.now().strftime('%y%b%d').upper()

def get_todays_weather_ticker(city):
    return tickers.get(city.upper()).upper() + '-' + get_date_in_kalshi_format()

def get_event_for_city(city):
    url = f"https://api.elections.kalshi.com/trade-api/v2/events/{get_todays_weather_ticker(city)}"
    response = make_signed_request_get(url)
    if response.get("error"):
        raise ValueError("Invalid city")
    return response