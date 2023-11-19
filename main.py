import logging
import sys
from bili import Bili
import config
from pprint import pprint

def setup_logging():
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    rootLogger = logging.getLogger()
    fileHandler = logging.FileHandler("dbiliown.log")
    fileHandler.setFormatter(formatter)
    rootLogger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
    rootLogger.addHandler(consoleHandler)

if __name__ == '__main__':
    setup_logging()
    conf = config.Config("dbiliown.yml")
    pprint(vars(conf))
    b = Bili(conf)
    pprint(b.user_videos(12522755, from_ts=1699456385))

