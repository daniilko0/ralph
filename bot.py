"""
:project: ralph
:version: see VERSION.txt
:authors: dadyarri & 6a16ec
:contact: https://vk.me/dadyarri & https://vk.me/6a16ec
:license: MIT

:copyright: (c) 2019 - 2020 dadyarri & 6a16ec

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

import json
import logging
import os
import random
from binascii import Error as binErr
from typing import List
from typing import NoReturn
from typing import Tuple

import gspread
import requests
import vk_api
from oauth2client.service_account import ServiceAccountCredentials
from vk_api.bot_longpoll import VkBotEventType

from db import Database
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
        self.log.setLevel(self.log_level)

        log_format = "%(asctime)s %(levelname)s: %(message)s"
        logging.basicConfig(format=log_format, datefmt="%d-%m-%Y %H:%M:%S")

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
            self.db = Database(self.db_url)
            self.db.connect()
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

        # API ключ Dialogflow (Искусственный интеллект)
        self.df_key = os.environ["DIALOGFLOW"]

        # Переименование обрабатываемых типов событий
        self.NEW_MESSAGE = VkBotEventType.MESSAGE_NEW
        self.NEW_POST = VkBotEventType.WALL_POST_NEW

        self.log.info(
            f"Беседа... {'Тестовая' if self.cid.endswith('1') else 'Основная'}"
        )

        self.log.info("Обновление версии в статусе группы...")
        try:
            with open("VERSION.txt", "r") as f:
                v = f"Версия: {f.read()}"
            self.user_vk.status.set(text=v, group_id=self.gid)
        except vk_api.exceptions.ApiError as e:
            self.log.error(f"Ошибка {e.__str__()}")
        else:
            self.log.info(f"Успех.")
        self.log.info("Инициализация завершена.")

    def send_message(
        self,
        msg: str,
        pid: int = None,
        keyboard: str = "",
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
            self.log.error(msg=e.__str__())
        except FileNotFoundError as e:
            self.log.error(msg=e)

    def send_mailing(self, msg: str = "", attach: str = None) -> NoReturn:

        """
        Отправка рассылки всем пользователям, активировавшим бота
        """

        if msg == "":
            msg = "Это просто тест."
        pids = ",".join(self._get_conversations_ids())
        self.send_message(msg=msg, attachments=attach, user_ids=pids)

    def _get_conversations_ids(self) -> list:
        """
        Получает идентификаторы пользователей последних 200 диалогов
        """
        q = self.bot_vk.messages.getConversations(offset=1, count=200,
                                                  group_id=self.gid)
        _l = []
        for i in range(len(q["items"])):
            if q["items"][i]["conversation"]["can_write"]["allowed"]:
                _l.append(str(q["items"][i]["conversation"]["peer"]["id"]))
        return _l

    def send_call(self) -> NoReturn:

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
                    msg=f"Cтуденты призваны.", pid=self.event.object.from_id
                )
                self.mode = "wait_for_command"

        else:
            self.send_message(
                msg="У тебя нет доступа к этой функции.", pid=self.event.object.from_id
            )

    def send_conversation(self) -> NoReturn:

        """
        Сообщает, какая беседа активна (тестовая или основная)

        Важно: Требует права администратора.
        """
        if self.current_is_admin():
            if self.cid == "2000000001":
                self.send_message(
                    msg="Тестовая беседа активна.", pid=self.event.object.from_id
                )
            if self.cid == "2000000002":
                self.send_message(
                    msg="Основная беседа активна.", pid=self.event.object.from_id
                )
        else:
            self.send_message(
                msg="У тебя нет доступа к этой функции.", pid=self.event.object.from_id
            )

    def handle_table(self, col: int) -> Tuple[str, str, str]:
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

    def get_debtors(self, col: int) -> NoReturn:
        """
        Призывает должников
        """
        self.send_message(
            msg="Эта команда может работать медленно. Прошу немного подождать.",
            pid=self.event.object.from_id,
        )
        men, cash, goal = self.handle_table(col)
        msg = f"{men} вам нужно принести по {cash} на {goal.lower()}."
        self.send_message(msg=msg, pid=self.cid)
        self.send_gui(text="Команда успешно выполнена.")

    def get_users_info(self, ids: list) -> List[dict]:
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
        """
        Меняет активную беседу
        """
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
                msg="У тебя нет доступа к этой функции.", pid=self.event.object.from_id
            )

    def current_is_admin(self) -> bool:
        """
        Проверяет, является ли текущий пользователь администратором бота
        """
        return str(self.event.object.from_id) in self.admins

    def send_gui(self, text: str = "Привет!") -> NoReturn:
        """
        Отправляет клавиатуру в зависимости от статуса пользователя
        """
        if self.current_is_admin():
            self.send_message(
                msg=text,
                pid=self.event.object.from_id,
                keyboard="keyboards/admin.json",
            )
        else:
            self.send_message(
                msg=text, pid=self.event.object.from_id, keyboard="keyboards/user.json",
            )
        self.mode = "wait_for_command"

    def ask_for_msg(self):
        self.mode = "ask_for_msg"
        if self.current_is_admin():
            self.send_message(
                msg="Отправьте сообщение с текстом объявления"
                "(вложения пока не поддерживаются).",
                pid=self.event.object.from_id,
                keyboard=open("keyboards/empty.json", "r", encoding="UTF-8").read(),
            )

    def show_msg(self, text: str):
        self.text = text
        self.send_message(
            msg=text, pid=self.event.object.from_id, keyboard="keyboards/prompt.json",
        )
