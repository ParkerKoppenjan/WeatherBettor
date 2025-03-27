# TO DO
# Keep a log of success rates
# Change temp based off time

import requests
from utils import discord
import datetime

headers = {
    "User-Agent": "WeatherBettor (me@elliotjarnit.dev, parkerkoppenjan@gmail.com)"
}

token_cache = None
cookie_cache = None

last_dsm_id = None
last_cli_id = None

fake_headers = {
    "Referer": "https://wethr.net/market/losangeles",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}

# Geographic coordinates for each city where bets can be placed (not always airport)
city_coords = {
    "LA" : (33.9422,-118.4036),
    "AUSTIN" : (30.1941, -97.6711),
    "DENVER" : (39.8563, -104.6764),
    "MIAMI" : (25.7923, -80.2823),
    "CHICAGO" : (41.7868, -87.7522),
    "PHILADELPHIA" : (39.8730, -75.2437),
    "NYC" : (40.7826, -73.9656)
}

city_stations = {
    "LA" : "KLAX",
    "AUSTIN": "KAUS",
    "DENVER": "KDEN",
    "MIAMI": "KMIA",
    "CHICAGO": "KLOT",
    "PHILADELPHIA": "KPHL",
    "NYC": "KNYC"
}

# Cache for API responses to reduce API calls
points_response_cache = {}
temperature_cache = 0

def get_points(city, force = False):
    """
    Get geographic point data from the NWS API for a given city.
    Uses cached data unless forced to refresh.

    Args:
        city (str): City to get point data for
        force (bool): Whether to force a fresh API call instead of using cache

    Returns:
        dict: JSON response from the NWS API, with point data
    """

    global points_response_cache

    if city in points_response_cache and not force:
        return points_response_cache[city]
    lat, long = city_coords[city.upper()]
    url = f"https://api.weather.gov/points/{lat},{long}"
    response = requests.get(url, headers=headers)
    points_response_cache[city] = response.json()
    return response.json()

def refresh_wethr_token():
    global token_cache
    global cookie_cache

    html_req = requests.get("https://wethr.net/market/losangeles", headers=fake_headers)
    html = html_req.text

    token_index = html.find("const API_TOKEN = '")
    token = html[token_index + len("const API_TOKEN = '"):html.find("';", token_index)]
    token_cache = token

    cookie = html_req.headers.get("Set-Cookie")
    cookie = cookie[:cookie.find(";")]
    cookie_cache = cookie

    discord.send_webhook("Wethr token fetched", f"New Token: {token}\nNew Cookie: {cookie}")
    print(f"Wethr token fetched: {token}")

def get_forecasted_highest_temperature(city):
    """
    Get the forecasted high temperature (F) for a city from the National Weather Service.
    """
    data = get_points(city)
    forecast_url = data.get("properties").get("forecast")
    forecast_response = requests.get(forecast_url, headers=headers)
    forecast_data = forecast_response.json()
    high = forecast_data.get("properties").get("periods")[0].get("temperature")
    return high

def get_current_temp_from_wethr(city):
    global token_cache
    global last_dsm_id
    global last_cli_id

    if token_cache is None:
        refresh_wethr_token()

    # Get date in format YYYY-MM-DD
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    station = city_stations.get(city.upper())

    url = f"http://wethr.net/marketv2.php?action=fetch_asos_data&station={station}&date={date}&timezone=America/Los_Angeles&token={token_cache}"
    headers = fake_headers
    headers["Cookie"] = cookie_cache
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        refresh_wethr_token()
        return get_current_temp(city)

    json = response.json()
    latest_observation = json[-1]

    # Find the latest observation that has a dsm_high_fahrenheit or cli_high_fahrenheit
    for observation in reversed(json):
        if observation.get("cli_high_fahrenheit"):
            if last_cli_id != observation.get("id"):
                temp = observation.get("cli_high_fahrenheit")
                discord.send_webhook("CLI TEMP FOUND", f"Temp: {temp}")
                last_cli_id = observation.get("id")
                return temp
            last_cli_id = observation.get("id")
        if observation.get("dsm_high_fahrenheit"):
            if last_dsm_id != observation.get("id"):
                temp = observation.get("dsm_high_fahrenheit")
                discord.send_webhook("DSM TEMP FOUND", f"Temp: {temp}")
                last_dsm_id = observation.get("id")
                return temp
            last_dsm_id = observation.get("id")

    if latest_observation.get("lowest_possible"):
        return latest_observation.get("lowest_possible")

    return None

def get_current_temp(city):
    global temperature_cache
    temp = get_current_temp_from_wethr(city)
    if temp is None:
        return temperature_cache
    temperature_cache = temp
    print(f"Current temp in {city}: {temp}")
    return temp
