"""

Info about logging levels:

DEBUG: Detailed information, typically of interest only when diagnosing problems.

INFO: Confirmation that things are working as expected.

WARNING: An indication that something unexpected happened, or indicative of some
problem in the near future (e.g. ‘disk space low’). The software is still working
as expected.

ERROR: Due to a more serious problem, the software has not been able to perform
some function.

CRITICAL: A serious error, indicating that the program itself may be unable to
continue running.

"""

import logging
import os
import sys
import traceback
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from logging import Formatter
from logging import Handler
from logging import LogRecord

import requests


class TelegramHandler(Handler):
    def emit(self, record: LogRecord) -> None:
        log_entry = self.format(record)
        token = os.environ["TG_TOKEN"]
        chat_ids = os.environ["TG_CHATS"].split(",")
        notifications = False
        if record.levelno < 30:
            notifications = True
        for chat in chat_ids:
            requests.get(
                f"https://api.telegram.org/bot{token}/sendMessage",
                params={
                    "chat_id": chat,
                    "text": log_entry,
                    "parse_mode": "markdown",
                    "disable_notification": notifications,
                },
            )


class TelegramFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        message = record.msg
        levelname = record.levelname
        module = record.module
        timestamp = datetime.utcfromtimestamp(record.created)
        ts = (
            timestamp.replace(tzinfo=timezone.utc)
            .astimezone(tz=timezone(timedelta(hours=3)))
            .strftime("%d.%m.%Y %H:%M:%S")
        )
        fmt = f"[{levelname}] ({module}): {ts} {message}"
        if record.exc_info:
            fmt += f"\n{record.exc_info[1].__repr__()}"
        return fmt


class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

    def init(self):
        self.logger.setLevel("INFO")
        console = logging.StreamHandler()
        formatter = TelegramFormatter()
        console.setFormatter(formatter)
        self.logger.addHandler(console)
        if "PRODUCTION" in os.environ:
            tg = TelegramHandler()
            tg.setFormatter(formatter)
            self.logger.addHandler(tg)
        return self.logger
