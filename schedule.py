from datetime import datetime
from datetime import timedelta

import requests
from bs4 import BeautifulSoup


class Date:
    @property
    def today(self):
        return datetime.today().strftime("%Y-%m-%d")

    @property
    def tomorrow(self):
        return datetime.strftime(datetime.now() + timedelta(1), "%Y-%m-%d")


class Schedule:
    def __init__(self, date: str):
        self.date = date
        self.warn = "Составлено, но не опубликовано."
        self.err = "Отсутствует."
        self.found = "Найдено."

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
