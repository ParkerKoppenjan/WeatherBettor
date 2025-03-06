from abc import ABC, abstractmethod

# Use string literal type hints to avoid actual imports
class Algorithm(ABC):
    NAME = "Unnamed Algorithm"
    VERSION = "0.1"
    LOOP_INTERVAL = 60
    running = True

    @abstractmethod
    def init(self, market: "kalshi.Market"):
        pass

    @abstractmethod
    def loop(self, market: "kalshi.Market"):
        pass

    def stop(self):
        self.running = False

