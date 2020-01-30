import re
import time
from datetime import datetime
from datetime import timedelta

import requests
from bs4 import BeautifulSoup

from bot import Bot
from logger import Logger

bot = Bot()


class Date:
    def __init__(self):
        self.today = datetime.today().strftime("%Y-%m-%d")
        self.day_after_tomorrow = datetime.strftime(
            datetime.now() + timedelta(2), "%Y-%m-%d"
        )

    @property
    def tomorrow(self):
        if datetime.today().weekday() == 5:
            return self.day_after_tomorrow
        return datetime.strftime(datetime.now() + timedelta(1), "%Y-%m-%d")


def pause():
    hour = datetime.now().hour
    p = 0
    if 0 <= hour <= 5:
        p = 5
    if 5 < hour < 10:
        p = 24
    if 9 < hour < 15:
        p = 19
    if 14 < hour < 19:
        p = 15
    if 18 < hour <= 23:
        p = 11
    time.sleep(p * 3600)


class Schedule:
    def __init__(self, date: str, gid: str = "324"):

        self.log = Logger()

        self.date = date

        try:
            self.raw = requests.get(
                f"http://rating.ivpek.ru/timetable/timetable/show?gid={gid}&date={date}"
            ).text
        except requests.exceptions.ConnectionError as e:
            self.log.log.error(msg=e)
        else:
            self.s = BeautifulSoup(self.raw, "lxml")

    def make_schedule(self):
        for span in self.s.find_all("span", {"class": "ldur"}):
            span.decompose()
        for br in self.s.find_all("br"):
            self.s.br.insert_before(" ")
            br.decompose()
        schedule_html = self.s.find_all("table", {"class": "tbl"})[1]
        schedule = []
        rows = schedule_html.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            cols = [el.text.strip() for el in cols]
            schedule.append([el for el in cols if el])
        schedule = [el for el in schedule if len(el) > 1]

        msg = ""
        replacements = {
            "Лекция": "(Л)",
            "Лабораторная работа": "(Л/Р)",
            "Зачет": "(З)",
            "Диф. зачет": "(ДифЗ)",
            "Диф.зачет": "(ДифЗ)",
            "Экзамен": "(Э)",
            "(английский язык)": "",
        }
        for i in range(len(schedule)):
            for j in range(len(schedule[i])):
                item = schedule[i][j]
                for k, v in replacements.items():
                    item = re.sub(k, v, item)
                if re.findall("Иностранный язык", item):
                    lesson = re.compile(r"(?<=\()\D+(?=\))").findall(item)
                    item = (
                        f"Английский язык ({lesson[1]}) "
                        f"Кузнецова И.Н/Коротина М.А. 12/13а"
                    )
                    schedule[i][j + 1] = ""
                msg += f"{item} "
            msg += "\n"
            if msg != "":
                msg = f"Расписание на {self.date}\n" + msg
        return msg

    def check(self):
        warn = self.s.find_all("div", {"class": "msg warning"})
        err = self.s.find_all("div", {"class": "msg error"})
        if warn or err:
            self.log.log.info("Расписание отсутствует.")
            return None
        self.log.log.info("Расписание составлено.")
        return self.s

    def get(self):
        if self.check() is not None:
            sch = self.make_schedule()
            if sch != "":
                return sch
            else:
                return "Расписание отсутствует."
        else:
            return "Расписание отсутствует."

    def listen(self):
        while True:
            if self.check() is not None:
                sch = self.make_schedule()
                self.log.log.info("Расписание отправлено.")
                bot.send_message(msg=sch, pid=bot.cid)
                bot.send_mailing(msg=sch)
                pause()
            else:
                time.sleep(15 * 60)


if __name__ == "__main__":
    d = Date()
    a = Schedule(d.tomorrow)
    a.listen()
