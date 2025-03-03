import requests
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
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

def sign_pss_text(private_key: rsa.RSAPrivateKey, text: str) -> str:
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

class Range:
    def __init__(self, ticker, low, high):
        self.ticker = ticker
        self.low = low
        self.high = high

    def number_in_range(self, number):
        return (self.low is None or number > self.low) and (self.high is None or number < self.high)

def get_date_in_kalshi_format():
    return datetime.now().strftime('%y%b%d').upper()

def get_todays_weather_ticker(city):
    return tickers.get(city.upper()).upper() + '-' + get_date_in_kalshi_format()

def get_event_for_city(city):
    url = f"https://api.elections.kalshi.com/trade-api/v2/events/{get_todays_weather_ticker(city)}"
    return make_signed_request_get(url)

def get_ranges_for_city(city):
    event = get_event_for_city(city)
    markets = event.get("markets")
    ranges = []

    for market in markets:
        name = market.get("yes_sub_title")
        degreeCount = name.count('°')

        if degreeCount == 1:
            if name.count('above') > 0:
                ranges.append(Range(market.get("ticker"), int(name.split('°')[0]), None))
            else:
                ranges.append(Range(market.get("ticker"), None, int(name.split('°')[0])))
        else:
            range_split = name.split('to')
            range1 = int(range_split[0].split('°')[0])
            range2 = int(range_split[1].split('°')[0])
            ranges.append(Range(market.get("ticker"), range1, range2))

    return ranges
