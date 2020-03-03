import logging.config
from pprint import pprint
from typing import NoReturn

import yaml


class Logger:
    def __init__(self):
        try:
            with open("logger.yml", "r") as f:
                self.config = yaml.safe_load(f.read())
        except FileNotFoundError:
            with open("logger/logger.yml", "r") as f:
                self.config = yaml.safe_load(f.read())
        pprint(self.config)
        self.log = logging.getLogger("tg")
        logging.config.dictConfig(config=self.config)


if __name__ == "__main__":
    logger = Logger()
    logger.log.warning("Test.")

    try:
        a = 3 / 0
    except ZeroDivisionError:
        logger.log.exception("Divizion By Zero")
