import time
import datetime
import utils.weather as weather
import utils.discord as discord
from algorithms.original import OriginalAlgorithm
from utils.kalshi import Market
import settings

def main():
    print("Weather Bettor v0.1")
    print("Created by: @elliotjarnit and @ParkerKoppenjan")
    print("Starting at " + str(datetime.datetime.now()))
    print("Selected market: " + settings.SELECTED_MARKET + "\n")
    print("Algorithm: " + settings.ALGORITHM.NAME + " " + settings.ALGORITHM.VERSION)

    discord.send_webhook("Bot Started",
                         "Bot started successfully on " + settings.SELECTED_MARKET + "\n" +
                         "Algorithm: " + settings.ALGORITHM.NAME + " " + settings.ALGORITHM.VERSION
                         )

    # Set up the market to bet on and the algorithm to use
    market = Market(settings.SELECTED_MARKET)
    algorithm = settings.ALGORITHM()

    # Initialize the algorithm
    algorithm.init(market)

    last_run = time.time()
    while algorithm.running:
        seconds_since_epoch = time.time()
        if (seconds_since_epoch - last_run) > settings.ALGORITHM.LOOP_INTERVAL:
            print(f"{settings.SELECTED_MARKET} - {time.strftime('%H:%M:%S', time.localtime())}")
            algorithm.loop(market)
            print()
            last_run = seconds_since_epoch

        time.sleep(0.5)


if __name__ == '__main__':
    try:
        main()
    except:
        discord.send_webhook("Bot Crashed", "An error occurred, stopping the bot.")









