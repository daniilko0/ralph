import re
import time
from datetime import datetime
from datetime import timedelta

import requests
from bs4 import BeautifulSoup


class Date:
    def __init__(self):
        self.today = datetime.today().strftime("%Y-%m-%d")
        self.tomorrow = datetime.strftime(datetime.now() + timedelta(1), "%Y-%m-%d")


class Schedule:
    def __init__(self, date: str):

    @property
    def status(self):
        raw = requests.get(
            f"http://rating.ivpek.ru/timetable/timetable/show?gid=324&date={self.date}"
        ).text
        s = BeautifulSoup(raw, "lxml")
        if s.find_all("div", {"class": "msg warning"}):
            return self.warn
        if s.find_all("div", {"class": "msg error"}):
            return self.err
        return self.found
