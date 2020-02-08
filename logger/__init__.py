import logging
import os
from typing import NoReturn


class Logger:
    def __init__(
        self,
        level: str = os.environ["LOG_LEVEL"],
        file: str = "",
        logfmt: str = os.environ["LOG_FMT"],
        datefmt: str = "%d-%m-%Y %H:%M:%S",
    ) -> NoReturn:

        """
        Инициализация и настройка logging
        :param level: Уровень логгирования
        :param file: Файл для записи логов
        :param logfmt: Формат логов
        :param datefmt: Формат даты/времени
        """
        self.log = logging.getLogger()
        self.log.setLevel(int(level))
        logging.basicConfig(filename=file, format=logfmt, datefmt=datefmt)
