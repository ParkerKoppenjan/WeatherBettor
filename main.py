import weather
import kalshi

cities = ["LA", "AUSTIN", "DENVER", "MIAMI", "CHICAGO", "PHILADELPHIA", "NYC"]

def main():
    for city in cities:
        forecasted_high = weather.get_forecasted_highest_temperature(city)
        current_temp = weather.get_current_temp(city)
        print(f"\n\n{city}")
        print(f"Forecasted high: {forecasted_high}")
        print(f"Current temp: {current_temp}")


if __name__ == "__main__":
    main()