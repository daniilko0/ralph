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

        self.raw = requests.get(
            f"http://rating.ivpek.ru/timetable/timetable/show?gid=324&date={date}"
        ).text
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
        return msg

    def check(self):
        warn = self.s.find_all("div", {"class": "msg warning"})
        err = self.s.find_all("div", {"class": "msg error"})
        if warn or err:
            return None
        return self.s

    def listen(self):
        while True:
            if self.check() is not None:
                sch = self.make_schedule()
                print(sch)
                time.sleep(24 * 3600)
            else:
                time.sleep(15 * 60)


if __name__ == "__main__":
    d = Date()
    a = Schedule(d.today)
    a.listen()
