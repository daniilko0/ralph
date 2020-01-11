"""
:project: ralph
:version: see VERSION.txt
:authors: dadyarri & 6a16ec
:contact: https://vk.me/dadyarri & https://vk.me/6a16ec
:license: MIT

:copyright: (c) 2019 - 2020 dadyarri & 6a16ec


"""

# DEBUG: Detailed information, typically of interest only when diagnosing problems.

# INFO: Confirmation that things are working as expected.

# WARNING: An indication that something unexpected happened, or indicative of some
# problem in the near future (e.g. ‘disk space low’). The software is still working
# as expected.

# ERROR: Due to a more serious problem, the software has not been able to perform
# some function.

# CRITICAL: A serious error, indicating that the program itself may be unable to
# continue running.

import json
import os
import random
import re
from binascii import Error as binErr
from typing import NoReturn
from typing import Union
import logging

import gspread
import pendulum
import requests
import vk_api
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from vk_api.bot_longpoll import VkBotEventType

from db.database import Database
from students import students
from vkbotlongpoll import RalphVkBotLongPoll


class Bot:
    """
    Класс, описывающий объект бота, включая авторизацию в API, и все методы бота.
    """

    def __init__(self) -> None:

        self.log_level = int(os.environ["LOG_LEVEL"])

        # Инициализация и настройка logging
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)

        log_format = "%(asctime)s %(levelname)s: %(message)s"
        logging.basicConfig(
            filename="ralph.log", format=log_format, datefmt="%d-%m-%Y %H:%M:%S"
        )

        self.log.info("Инициализация...")

        self.token = os.environ["VK_TOKEN"]
        self.user_token = os.environ["VK_USER_TOKEN"]
        self.gid = os.environ["GID_ID"]
        self.cid = os.environ["CID_ID"]
        self.table = os.environ["TABLE_ID"]
        self.db_url = os.environ["DATABASE_URL"]

        # Авторизация в PostgreSQL - базе данных

        self.log.info("Авторизация базы данных...")
        try:
            db = Database(self.db_url)
            db.connect()
        except TypeError:
            self.log.error("Неудача. Ошибка авторизации.")
        else:
            self.log.info("Успех.")

        # Авторизация в API ВКонтакте
        self.log.info("Авторизация ВКонтакте...")
        try:
            self.bot_session = vk_api.VkApi(token=self.token, api_version="5.103")
            self.user_session = vk_api.VkApi(token=self.user_token, api_version="5.103")
        except vk_api.exceptions.AuthError:
            self.log.error("Неудача. Ошибка авторизации.")
        else:
            try:
                self.bot_vk = self.bot_session.get_api()
                self.user_vk = self.user_session.get_api()
                self.longpoll = RalphVkBotLongPoll(
                    vk=self.bot_session, group_id=self.gid
                )
            except requests.exceptions.ConnectionError:
                self.log.error("Неудача. Превышен лимит попыток подключения.")
            except vk_api.exceptions.ApiError:
                self.log.error("Неудача. Ошибка доступа.")
            else:
                self.log.info("Успех.")
                self.log.debug(f"Версия API ВКонтакте: {self.bot_session.api_version}.")

        # Инициализация дополнительных переменных
        self.event = {}
        self.admins = os.environ["ADMINS_IDS"].split(",")

        self.mode = ""
        self.text = ""
        self.ids = []

        # Авторизация в API Google Sheets и подключение к заданной таблице
        self.log.info("Авторизация в Google Cloud...")
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                keyfile_dict=json.loads(os.environ["GOOGLE_CREDS"]), scopes=self.scope
            )
        except binErr:
            self.log.error("Неудача.")
        else:
            self.gc = gspread.authorize(credentials=credentials)
            self.table_auth = self.gc.open_by_key(key=self.table)
            self.sh = self.table_auth.get_worksheet(0)
            self.sh_sch = self.table_auth.get_worksheet(1)
            self.log.info("Успех.")

        self.df_key = os.environ["DIALOGFLOW"]

        # Переименование обрабатываемых типов событий
        self.NEW_MESSAGE = VkBotEventType.MESSAGE_NEW
        self.NEW_POST = VkBotEventType.WALL_POST_NEW

        self.log.info("Беседа...")
        self.log.info("Тестовая" if self.cid == "2000000001" else "Основная")

        self.log.info("Обновление версии в статусе группы...")
        try:
            with open("VERSION.txt", "r") as f:
                v = f"Версия: {f.read()}"
            self.user_vk.status.set(text=v, group_id=self.gid)
        except vk_api.exceptions.ApiError as e:
            self.log.error(f"Ошибка {e.__str__()}")
        else:
            self.log.info(f"Успех. {v}.")
        self.log.info("Инициализация завершена.")
        self.send_message(msg="Инициализация... Успех.", pid=self.admins[0])

    def send_message(
        self,
        msg: str,
        pid: int = None,
        keyboard="",
        attachments: str = None,
        user_ids: str = None,
    ) -> NoReturn:

        """
        Отправка сообщения msg пользователю/в беседу pid
        с клавиатурой keyboard (не отправляется, если не указан json файл)
        """

        kb = open(keyboard, "r", encoding="UTF-8").read() if keyboard != "" else ""

        try:
            self.bot_vk.messages.send(
                peer_id=pid,
                random_id=random.getrandbits(64),
                message=msg,
                keyboard=kb,
                attachments=attachments,
                user_ids=user_ids,
            )

        except vk_api.exceptions.ApiError as e:
            self.log.error(f"[ОШИБКА]: {e.__str__()}")
        except FileNotFoundError:
            self.log.error("Такого файла не существует.")

    def send_mailing(self, msg: str = "", attach: str = None):
        if msg == "":
            msg = "Это просто тест."
        pids = ",".join(self.get_conversations_ids())
        self.send_message(msg=msg, attachments=attach, user_ids=pids)

    def get_conversations_ids(self):
        q = self.bot_vk.messages.getConversations(count=200, group_id=self.gid)
        _l = []
        for i in range(len(q["items"])):
            if q["items"][i]["conversation"]["can_write"]["allowed"]:
                _l.append(q["items"][i]["conversation"]["peer"]["id"])
        self.log.debug(_l)
        return _l

    def send_call(self) -> None:

        """
        Призывает всех студентов в активной беседе.

        Важно: Требует права администратора.
        """
        if self.current_is_admin():
            self.mode = "execute"
            members = self.generate_mentions(list(students.keys()), names=False)
            if members is not None:
                self.mode = "wait_for_command"
                self.send_message(
                    msg=members, pid=self.cid,
                )
                self.send_message(
                    pid=self.event.object.from_id, msg=f"Cтуденты призваны."
                )
                self.mode = "wait_for_command"

        else:
            self.send_message(
                pid=self.event.object.from_id, msg="У тебя нет доступа к этой функции.",
            )

    def send_conversation(self) -> None:

        """
        Сообщает, какая беседа активна (тестовая или основная)

        Важно: Требует права администратора.
        """
        if self.current_is_admin():
            if self.cid == "2000000001":
                self.send_message(
                    pid=self.event.object.from_id, msg="Тестовая беседа активна."
                )
            if self.cid == "2000000002":
                self.send_message(
                    pid=self.event.object.from_id, msg="Основная беседа активна."
                )
        else:
            self.send_message(
                pid=self.event.object.from_id, msg="У тебя нет доступа к этой функции."
            )

    def get_schedule_for_tomorrow(self) -> None:
        """
        Получает строку с завтрашней датой (послезавтрашней, если сегодня суббота) и вы-
        зывает self.get_schedule()
        """
        dow = pendulum.now("Europe/Moscow").format("d")
        a = 1
        if dow == "6":
            a = 2
        date = pendulum.now("Europe/Moscow").add(days=a).format("YYYY-MM-DD")
        self.get_schedule(date=date)

    def get_schedule(self, date: Union[str, bool] = False) -> None:
        """
        Запрашивает расписание на указанную дату у сервера.
        """
        if not date:
            date = pendulum.now("Europe/Moscow").format("YYYY-MM-DD")
        pid = self.event.object.from_id
        req = requests.get(
            f"http://rating.ivpek.ru/timetable/timetable/show?gid=324&date={date}"
        )
        soup = BeautifulSoup(req.text, "lxml")
        msg_w = soup.find_all("div", {"class": "msg warning"})
        msg_e = soup.find_all("div", {"class": "msg error"})
        if msg_w != [] and msg_w is not None:
            self.send_message(pid=pid, msg=msg_w[0].text)
        elif msg_e != [] and msg_e is not None:
            self.send_message(pid=pid, msg=msg_e[0].text)
        else:
            for span in soup.find_all("span", {"class": "ldur"}):
                span.decompose()
            for br in soup.find_all("br"):
                soup.br.insert_before(" ")
                br.decompose()
            schedule_html = soup.find_all("table", {"class": "tbl"})[1]
            schedule = []
            rows = schedule_html.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                cols = [el.text.strip() for el in cols]
                schedule.append([el for el in cols if el])
            schedule = [el for el in schedule if len(el) > 1]

            sch_date = soup.find_all("span", {"class": "yellow-msg"})[1].text
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

            if not msg:
                msg = "Расписание отсутствует."
            else:
                msg = f"Расписание на {sch_date}:\n{msg}"
            self.send_message(pid=pid, msg=msg)

    def handle_table(self, col):
        men, cash, goal = None, None, None
        try:
            self.gc.login()
            debtor_ids = []
            for i in range(5, 38):
                if self.sh.cell(i, col).value != self.sh.cell(41, col).value:
                    debtor_ids.append(self.sh.cell(i, 3).value)
        except gspread.exceptions.APIError as e:
            self.log.error(
                f"[ERROR]: [{e.response.error.code}] – {e.response.error.message}"
            )
            self.handle_table(col)
        except (AttributeError, KeyError, ValueError):
            self.log.error("Херню ты натворил, Даня!")
        else:
            men = self.generate_mentions(debtor_ids, True)
            cash = self.sh.cell(41, col).value
            goal = self.sh.cell(4, col).value
        if men is not None and cash is not None and goal is not None:
            return men, cash, goal
        else:
            self.handle_table(col)

    def get_debtors(self, col):
        self.send_message(
            pid=self.event.object.from_id,
            msg="Эта команда может работать медленно. Прошу немного подождать.",
        )
        men, cash, goal = self.handle_table(col)
        msg = f"{men} вам нужно принести по {cash} на {goal.lower()}."
        self.send_message(pid=self.cid, msg=msg)
        self.send_gui(text="Команда успешно выполнена.")

    def get_users_info(self, ids: list) -> list:
        """
        Получает информацию о пользователях с указанными id
        """
        return self.bot_vk.users.get(user_ids=",".join(map(str, ids)))

    def generate_mentions(self, ids: list, names: bool) -> str:
        """
        Генерирует строку с упоминаниями из списка идентификаторов
        """
        users_info = self.get_users_info(ids)
        users_names = [
            users_info[i]["first_name"] if names else "!" for i in range(len(ids))
        ]
        result = (", " if names else "").join(
            [f"@id{_id}({users_names[i]})" for (i, _id) in enumerate(ids)]
        )
        return result

    def change_conversation(self) -> str:
        if self.current_is_admin():
            if self.cid == "2000000001":
                self.cid = "2000000002"
                self.send_conversation()
                return self.cid
            elif self.cid == "2000000002":
                self.cid = "2000000001"
                self.send_conversation()
                return self.cid
        else:
            self.send_message(
                pid=self.event.object.from_id, msg="У тебя нет доступа к этой функции."
            )

    def current_is_admin(self) -> bool:
        """
        Проверяет, является ли текущий пользователь администратором бота
        """
        return str(self.event.object.from_id) in self.admins

    def send_gui(self, text: str = "Привет!"):
        if self.current_is_admin():
            self.send_message(
                pid=self.event.object.from_id,
                msg=text,
                keyboard="keyboards/admin.json",
            )
        else:
            self.send_message(
                pid=self.event.object.from_id, msg=text, keyboard="keyboards/user.json",
            )
        self.mode = "wait_for_command"

    def ask_for_msg(self):
        self.mode = "ask_for_msg"
        if self.current_is_admin():
            self.send_message(
                pid=self.event.object.from_id,
                msg="Отправьте сообщение с текстом объявления"
                "(вложения пока не поддерживаются).",
                keyboard=open("keyboards/empty.json", "r", encoding="UTF-8").read(),
            )

    def show_msg(self, text: str):
        self.text = text
        self.send_message(
            pid=self.event.object.from_id, msg=text, keyboard="keyboards/prompt.json",
        )
