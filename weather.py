# TO DO
# Grab NWS forecasted highs from LAX, Denver, etc.
# Grab available bets for areas on Kalshi
# Make bets +/- 1 degree from forecasted high.
# Available bets are usually a range of 1, so maybe bet on the averaged range closest to forecasted high?
# Maybe spread, either over multiple temps or multiple locations
# Analyze high periodically. If it changes, change bet.
# Keep a log of success rates

import requests

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

def get_todays_high(coordinates):
    lat, long = coordinates
    url = f"https://api.weather.gov/points/{lat},{long}"
    response = requests.get(url, headers=headers)
    data = response.json()
    forecast_url = data.get("properties").get("forecast")
    forecast_response = requests.get(forecast_url, headers=headers)
    forecast_data = forecast_response.json()
    high = forecast_data.get("properties").get("periods")[0].get("temperature")
    return high

def get_current_temp(coordinates : tuple) -> int:
    lat, long = coordinates
    url = f"https://api.weather.gov/points/{lat},{long}"
    response = requests.get(url, headers=headers)
    data = response.json()

    # get the station
    stations_url = data.get("properties").get("observationStations")
    stations_response = requests.get(stations_url, headers=headers)
    stations_data = stations_response.json()
    station_id = stations_data.get("features")[0].get("properties").get("stationIdentifier")

    obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
    obs_response = requests.get(obs_url, headers=headers)
    obs_data = obs_response.json()

    temp = obs_data.get("properties").get("temperature").get("value")  # in celsius (I HATE CELSIUS)
    if temp is not None:
        temp = round(temp * 9 / 5 + 32)  # convert to Fahrenheit
    return temp

def main():
    c = city_coords.get("LA")
    print(get_todays_high(c))
    print(get_current_temp(c))

if __name__ == "__main__":
    main()