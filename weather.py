# TO DO
# Grab NWS forecasted highs from LAX, Denver, etc.
# Grab available bets for areas on Kalshi
# Make bets +/- 1 degree from forecasted high.
# Available bets are usually a range of 1, so maybe bet on the averaged range closest to forecasted high?
# Maybe spread, either over multiple temps or multiple locations
# Analyze high periodically. If it changes, change bet.
# Keep a log of success rates
# Change temp based off time

import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

headers = {
    "User-Agent": "WeatherBettor (me@elliotjarnit.dev, parkerkoppenjan@gmail.com)"
}

# scooped up the coordinates for each betting location, not always the airport
city_coords = {
    "LA" : (33.9422,-118.4036),
    "AUSTIN" : (30.1941, -97.6711),
    "DENVER" : (39.8563, -104.6764),
    "MIAMI" : (25.7923, -80.2823),
    "CHICAGO" : (41.7868, -87.7522),
    "PHILADELPHIA" : (39.8730, -75.2437),
    "NYC" : (40.7826, -73.9656)
}

station_ids = {
    "LA": "KLAX",

}

points_response_cache = {}

def get_points(city, force = False):
    if city in points_response_cache and not force:
        return points_response_cache[city]
    lat, long = city_coords[city.upper()]
    url = f"https://api.weather.gov/points/{lat},{long}"
    response = requests.get(url, headers=headers)
    points_response_cache[city] = response.json()
    return response.json()

def get_forecasted_highest_temperature(city):
    data = get_points(city)
    forecast_url = data.get("properties").get("forecast")
    forecast_response = requests.get(forecast_url, headers=headers)
    forecast_data = forecast_response.json()
    high = forecast_data.get("properties").get("periods")[0].get("temperature")
    return high

def kelvin_to_fahrenheit(kelvin):
    return round((kelvin - 273.15) * (9 / 5) + 32)

def get_current_temp(city):
    lat, long = city_coords[city.upper()]

    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={long}&appid={os.environ["OPEN_WEATHER_API_KEY"]}"
    response = requests.get(url, headers=headers)
    json = response.json()

    temp = kelvin_to_fahrenheit(json["current"]["temp"])
    print(f"Current temp in {city}: {temp}")
    return temp

get_current_temp("LA")