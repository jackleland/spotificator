from slacker import Slacker
from spotipy import SpotifyException

class Spotificator(object):
    RESTART_INTERVAL = 1800.0

    def __init__(self):
        self.slacker = None
        self.restart()

    def restart(self):
        self.slacker = Slacker()

    def main(self):
        while True:
            try:
                self.slacker.main_loop()
            except SpotifyException:
                self.restart()
            except Exception:
                exit()


if __name__ == '__main__':
    Spotificator().main()