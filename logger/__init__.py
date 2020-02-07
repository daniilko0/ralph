import logging
import os


class Logger:
    def __init__(
        self,
        level=os.environ["LOG_LEVEL"],
        file="",
        logfmt=os.environ["LOG_FMT"],
        datefmt="%d-%m-%Y %H:%M:%S",
    ):

        # Инициализация и настройка logging
        self.log = logging.getLogger()
        self.log.setLevel(int(level))

        logging.basicConfig(filename=file, format=logfmt, datefmt=datefmt)
