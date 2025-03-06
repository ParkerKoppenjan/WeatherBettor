# TO DO
# Keep a log of success rates
# Change temp based off time

import requests
from dotenv import load_dotenv
import os
from utils import discord
import datetime

load_dotenv()


TOMORROW_IO_API_KEY = os.getenv("TOMORROW_IO_API_KEY")

headers = {
    "User-Agent": "WeatherBettor (me@elliotjarnit.dev, parkerkoppenjan@gmail.com)"
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
token_cache = None
cookie_cache = None
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

    html_req = requests.get("https://wethr.net/market/losangeles")
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

    if token_cache is None:
        refresh_wethr_token()

    # Get date in format YYYY-MM-DD
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    station = city_stations.get(city.upper())

    url = f"https://wethr.net/backend/fetch_asos_data.php?station={station}&date={date}&timezone=America/Los_Angeles&token={token_cache}"
    response = requests.get(url, headers={
        "Cookie": cookie_cache,
        "Referer": "https://wethr.net/market/losangeles",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    })

    if response.status_code != 200:
        refresh_wethr_token()
        return get_current_temp(city)

    json = response.json()
    latest_observation = json[-1]

    if latest_observation.get("cli_high_fahrenheit") and latest_observation.get("dsm_high_fahrenheit"):
        temp = max(latest_observation.get("cli_high_fahrenheit"), latest_observation.get("dsm_high_fahrenheit"))
        print("CLI TEMP")
        discord.send_webhook("CLI TEMP", f"CLI: {latest_observation.get('cli_high_fahrenheit')}\nDSM: {latest_observation.get('dsm_high_fahrenheit')}\nMax: {temp}")
        return temp

    if latest_observation.get("cli_high_fahrenheit"):
        temp = latest_observation.get("cli_high_fahrenheit")
        print("CLI TEMP")
        discord.send_webhook("CLI TEMP", f"CLI: {latest_observation.get('cli_high_fahrenheit')}")
        return temp

    if latest_observation.get("dsm_high_fahrenheit"):
        temp = latest_observation.get("dsm_high_fahrenheit")
        print("CLI TEMP")
        discord.send_webhook("CLI TEMP", f"DSM: {latest_observation.get('dsm_high_fahrenheit')}")
        return temp

    if latest_observation.get("highest_possible"):
        return latest_observation.get("highest_possible")

    if latest_observation.get("temperature_fahrenheit"):
        return latest_observation.get("temperature_fahrenheit")

    return None

def get_current_temp(city):
    global temperature_cache
    temp = get_current_temp_from_wethr(city)
    if temp is None:
        return temperature_cache
    temperature_cache = temp
    print(f"Current temp in {city}: {temp}")
    return temp

# def get_current_temp(city):
#     """
#     Get the current temperature for a city using some weird Mesowest API (or Tomorrow.io, or Open-METAR, if failure).
#     """
#     station = city_stations.get(city.upper())
#
#     # Primary: Mesowest API
#     url = f"https://api.mesowest.net/v2/stations/timeseries?STID={station}&showemptystations=1&units=temp|F,speed|mph,english&recent=60&token=95727a10ba0443c9bd8c15a6ccaed2d6&complete=1&obtimezone=local"
#     response = requests.get(url, headers=headers)
#
#     if response.status_code == 200:
#         json = response.json()
#         station_data = json["STATION"][0]
#         observations = station_data["OBSERVATIONS"]
#         temps = observations["air_temp_set_1"]
#
#         # Get the last temperature observation that isn't null
#         temp = None
#         for i in range(len(temps) - 1, -1, -1):
#             if temps[i] is not None:
#                 temp = round(temps[i])
#                 break
#         print(f"Current temp in {city}: {temp}")
#         return temp
#
#     print(f"Error getting current temp in {city} from Mesowest API, trying backup Tomorrow.io API.")
#
#     # Backup: Tomorrow.io API
#     if TOMORROW_IO_API_KEY:
#         url = f"https://api.tomorrow.io/v4/weather/realtime?location={city_coords[city.upper()][0]},{city_coords[city.upper()][1]}&units=imperial&apikey={TOMORROW_IO_API_KEY}"
#         response = requests.get(url)
#         if response.status_code == 200:
#             json = response.json()
#             temp = json["data"]["values"]["temperature"]
#             print(f"Current temp in {city}: {temp}")
#             return temp
#         else:
#             print(f"Error getting current temp in {city} from Tomorrow.io API, trying Open-METAR API.")
#
#     # Final Backup: Open-METAR API
#     url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=json"
#     response = requests.get(url)
#
#     if response.status_code == 200:
#         json = response.json()
#         station_data = json[0]
#         temp_celsius = station_data.get("temp")
#
#         if temp_celsius is not None:
#             temp = round((temp_celsius * 9/5) + 32)  # Convert °C to °F
#             print(f"Current temp in {city}: {temp}")
#             return temp
#
#     print(f"Error getting current temp in {city} from all sources.")
#     return None