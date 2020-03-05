import logging
from logging import Handler
from logging import LogRecord
from logging import Formatter
import os
from datetime import datetime, timezone, timedelta

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
                f"https://api.telegram.org/bot{token}/sendMessage?chat_id="
                f"{chat}&text"
                f"={log_entry}&parse_mode=markdown&disable_notification={notifications}"
            )


class TelegramFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        message = record.msg
        levelname = record.levelname
        timestamp = datetime.utcfromtimestamp(record.created)
        ts = (
            timestamp.replace(tzinfo=timezone.utc)
            .astimezone(tz=timezone(timedelta(hours=3)))
            .strftime("%d.%m.%Y %H:%M:%S")
        )
        log = f"[{levelname}]: {ts}\n{message}"
        if record.exc_info:
            log += f"\n{record.exc_info[1].__repr__()}"
        return log


def init_logger():
    logger = logging.getLogger()
    logger.setLevel("INFO")
    handler = TelegramHandler()
    formatter = TelegramFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
