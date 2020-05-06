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
from logging import Handler
from logging import LogRecord
from logging import Formatter
import os
from datetime import datetime, timezone, timedelta

import requests


class BaseFormatter(Formatter):
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
        formatter = BaseFormatter()
        console.setFormatter(formatter)
        self.logger.addHandler(console)
        return self.logger
