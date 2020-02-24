import os
import re
import time
from datetime import datetime
from datetime import timedelta
from typing import Union

import schedule
import requests
from bs4 import BeautifulSoup

from bot import Bot
from logger import Logger
from database import Database

bot = Bot()
log = Logger()


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
        log (Logger): Объект класса Logger, содержащий конфигурации модуля logging
        date (str): Дата в формате ГГГГ-ММ-ДД, используемая для получения расписания
        gid (str): Идентификатор группы, для которой нужно получать расписание        
    """

    def __init__(self, date: str, gid: str = "324"):
        self.log = Logger()
        self.date = date
        self.gid = gid

    def is_exist(self) -> bool:
        """
        Проверяет наличие расписания, основываясь на присутствии плашек
        "Расписание отстутствует" и "Расписание составлено, но не опубликовано"
        
        Returns:
            bool: Флаг, указывающий на существование расписания
        """
        soup = self.get_raw()
        warn = soup.find_all("div", {"class": "msg warning"})
        err = soup.find_all("div", {"class": "msg error"})
        if warn or err:
            self.log.log.info("Расписание отсутствует.")
            return False
        return True

    def get_raw(self) -> BeautifulSoup:
        """
        Получает с сервера веб-страницу с расписанием и возвращает объект
        веб-скрапера
        
        Returns:
            BeautifulSoup: Объект веб-скрапера, содержащий сырую веб-страницу с расписанием
        """
        request = requests.get(
            f"http://rating.ivpek.ru/timetable/timetable/show?gid={self.gid}&date"
            f"={self.date}"
        )
        try:
            if request.status_code != 200:
                self.log.log.error(
                    "Подключение неудачно. Автоматический повтор через 5 секунд."
                )
                raise requests.exceptions.ConnectionError
        except requests.exceptions.ConnectionError as e:
            self.log.log.error(msg=e)
            self.get_raw()
        else:
            soup = BeautifulSoup(request.text, "lxml")
            return soup

    def parse(self) -> Union[str, bool]:
        """Форматирует расписание в читаемую строку
        
        Returns:
            str: Если расписание найдено
            bool: Если расписание еще не опубликовано
        """
        soup = self.get_raw()
        for span in soup.find_all("span", {"class": "ldur"}):
            span.decompose()
        for br in soup.find_all("br"):
            soup.br.insert_before(" ")
            br.decompose()
        schedule_html = soup.find_all("table", {"class": "tbl"})[1]
        sch = []
        rows = schedule_html.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            cols = [el.text.strip() for el in cols]
            sch.append([el for el in cols if el])
        sch = [el for el in sch if len(el) > 1]

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
        if not msg:
            self.log.log.info("Расписание отсутствует.")
            return False
        date = datetime.strptime(self.date, "%Y-%m-%d").strftime("%d.%m.%Y")
        msg = f"Расписание на {date}:\n{msg}"
        return msg

    def send(self):
        """Отправляет расписание в активную беседу
        и в ЛС подписчикам рассылки "Расписание"
        """
        sch = self.parse()
        if sch:
            db = Database(os.environ["DATABASE_URL"])
            subscribers = db.fetch_subcribers("schedule")
            bot.send_message(msg=sch, pid=bot.cid)
            bot.send_mailing(ids=subscribers, msg=sch)


def listen():
    """Слушает сервер на предмет наличия расписания.
    Если находит - отправляет, иначе ждет 15 минут
    """
    d = Date()
    sch = Schedule(d.tomorrow)
    if sch.is_exist():
        if sch.parse():
            sch.send()
        else:
            log.log.info("Расписание отстутствует")
            time.sleep(15 * 60)
    else:
        log.log.info("Расписание отстутствует")
        time.sleep(15 * 60)


if __name__ == "__main__":
    schedule.every().day.at("09:20").do(listen)
    while True:
        schedule.run_pending()
