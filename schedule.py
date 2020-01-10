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
