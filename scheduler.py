import re
import os
import time
from datetime import datetime
from datetime import timedelta
from typing import List

import requests
import schedule
from bs4 import BeautifulSoup

from logger import Logger
from bot import Bot
from database import Database


class Date:
    """
    Вспомогательный класс, содержащий строковые представления дат
    """

    @property
    def today(self) -> str:
        """
        Возвращает сегодняшнюю дату в формате ГГГГ-ММ-ДД
        """
        return datetime.today().strftime("%Y-%m-%d")

    @property
    def day_after_tomorrow(self) -> str:
        """
        Возвращает послезавтрашнюю дату в формате ГГГГ-ММ-ДД
        """
        return datetime.strftime(datetime.now() + timedelta(2), "%Y-%m-%d")

    @property
    def tomorrow(self) -> str:
        """
        Возвращает послезавтрашнюю дату в формате ГГГГ-ММ-ДД,
        если сегодня суббота, завтрашнюю в любой другой день
        """
        if datetime.today().weekday() == 5:
            return self.day_after_tomorrow
        return datetime.strftime(datetime.now() + timedelta(1), "%Y-%m-%d")


class Schedule:

    """Класс, переводящий расписание из сырой веб-страницы в читаемую строку

    Attributes:
        date (str): Дата в формате ГГГГ-ММ-ДД, используемая для получения расписания
        gid (str): Идентификатор группы, для которой нужно получать расписание

    Example:
        .. code-block:: python

            d = Date() # Новый объект конструктора дат
            sch = Schedule(d.today) # Новый объект конструктора расписания
            sch.get_raw() # Соединение с сервером, получение свежего
            # расписания на сегодня
            if sch.is_exist():  # Проверка наличия расписания
                text = sch.generate() # Генерация расписания в читаемом виде
    """

    def __init__(self, date: str, gid: str = "324"):
        self.date = date
        self.gid = gid
        self.log = Logger().init()
        self.raw = None

    def get_raw(self):
        """Подключается к серверу и получает расписание как объект вебскрапера
        """
        request = requests.get(
            "http://rating.ivpek.ru/timetable/timetable/show",
            params={"date": self.date, "gid": self.gid},
        )
        soup = BeautifulSoup(request.text, "lxml")
        self.raw = soup

    def is_exist(self) -> bool:
        """
        Проверяет наличие расписания, основываясь на присутствии плашек
        "Расписание отстутствует" и "Расписание составлено, но не опубликовано" и
        содержимом таблицы с расписанием

        Returns:
            bool: Флаг, указывающий на существование расписания
        """
        soup = self.raw
        warn = soup.find_all("div", {"class": "msg warning"})
        err = soup.find_all("div", {"class": "msg error"})
        lessons = soup.find_all("div", {"id": "lesson"})
        if warn or err or not lessons:
            self.log.info("Расписание отсутствует.")
            return False
        return True

    def clean(self) -> List[list]:
        """Чистит объект вебскрапера от мусорных данных и оставляет только то,
        что относится к расписанию

        Returns:
            List[list]: Список со списками. Каждый вложенный список описывает пару (
            номер, название предмета, преподавателя, кабинет)
        """
        soup = self.raw
        for span in soup.find_all("span", {"class": "ldur"}):
            span.decompose()
        for br in soup.find_all("br"):
            soup.br.insert_before(" ")
            br.decompose()
        soup = soup.find_all("table", {"class": "tbl"})[1]
        sch = []
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            cols = [el.text.strip() for el in cols]
            sch.append([el for el in cols if el])
        sch = [el for el in sch if len(el) > 1]
        return sch

    def generate(self) -> str:
        """Собирает расписание в читаемую строку
        """
        sch = self.clean()
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
        for i in range(len(sch)):
            for j in range(len(sch[i])):
                item = sch[i][j]
                for k, v in replacements.items():
                    item = re.sub(k, v, item)
                if re.findall("Иностранный язык", item):
                    lesson = re.compile(r"(?<=\()\D+(?=\))").findall(item)
                    item = (
                        f"Английский язык ({lesson[1]}) "
                        f"Кузнецова И.Н/Коротина М.А. 12/13а"
                    )
                    sch[i][j + 1] = ""
                msg += f"{item} "
            msg += "\n"
        date = datetime.strptime(self.date, "%Y-%m-%d").strftime("%d.%m.%Y")
        msg = f"Расписание на {date}:\n{msg}"
        return msg


def send():
    """Отправляет расписание в активную беседу
    и в ЛС подписчикам рассылки "Расписание"
    """
    bot = Bot()
    bot.log.setLevel("ERROR")
    bot.auth()
    d = Date()
    s = Schedule(d.tomorrow)
    s.get_raw()
    sch = s.generate()
    chat = bot.db.get_active_chat_id(group=109)
    bot.send_mailing(m_id=2, text=sch, group=109)
    bot.send_message(msg=sch, pid=chat)


def listen():
    """Слушает сервер на предмет наличия расписания.
    Если находит - отправляет, иначе ждет 15 минут
    """
    d = Date()
    sch = Schedule(d.tomorrow)
    sch.get_raw()
    while not sch.is_exist():
        time.sleep(15 * 60)
        sch.get_raw()
    sch.log.info("Расписание опубликовано")
    send()


if __name__ == "__main__":
    schedule.every().day.at("11:00").do(listen)
    while True:
        schedule.run_pending()
