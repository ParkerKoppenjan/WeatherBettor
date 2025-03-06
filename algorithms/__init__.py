from abc import abstractmethod
from utils import kalshi

class Algorithm:
    NAME = "Unnamed Algorithm"
    VERSION = "0.1"
    LOOP_INTERVAL = 60

    running = True

    @abstractmethod
    def init(self, market: kalshi.Market):
        pass

    @abstractmethod
    def loop(self, market: kalshi.Market):
        pass

    def stop(self):
        self.running = False
