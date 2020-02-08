"""
:project: ralph
:version: see VERSION.txt
:authors: dadyarri, 6a16ec
:contact: https://vk.me/dadyarri, https://vk.me/6a16ec
:license: MIT

:copyright: (c) 2019 - 2020 dadyarri, 6a16ec

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


import os
import random
from typing import List
from typing import NoReturn

import requests
import vk_api
from vk_api.bot_longpoll import VkBotEventType

from keyboard import Keyboards
from logger import Logger
from vkbotlongpoll import RalphVkBotLongPoll


def auth(func):
    def wrapper(self):
        if not self.current_is_admin():
            self.send_gui(text="У тебя нет доступа к этой функции.")
        else:
            func(self)

    return wrapper


class Bot:
    """
    Класс, описывающий объект бота, включая авторизацию в API, и все методы бота.
    """

    def __init__(self) -> None:

        self.log = Logger()

        self.log.log.info("Инициализация...")

        self.token = os.environ["VK_TOKEN"]
        self.user_token = os.environ["VK_USER_TOKEN"]
        self.gid = os.environ["GID_ID"]
        self.cid = os.environ["CID_ID"]
        self.table = os.environ["TABLE_ID"]

        self.kbs = Keyboards()

        # Авторизация в API ВКонтакте
        self.log.log.info("Авторизация ВКонтакте...")
        try:
            self.bot_session = vk_api.VkApi(token=self.token, api_version="5.103")
            self.user_session = vk_api.VkApi(token=self.user_token, api_version="5.103")
        except vk_api.exceptions.AuthError:
            self.log.log.error("Неудача. Ошибка авторизации.")
        else:
            try:
                self.bot_vk = self.bot_session.get_api()
                self.user_vk = self.user_session.get_api()
                self.longpoll = RalphVkBotLongPoll(
                    vk=self.bot_session, group_id=self.gid
                )
            except requests.exceptions.ConnectionError:
                self.log.log.error("Неудача. Превышен лимит попыток подключения.")
            except vk_api.exceptions.ApiError:
                self.log.log.error("Неудача. Ошибка доступа.")
            else:
                self.log.log.info("Успех.")
                self.log.log.debug(
                    f"Версия API ВКонтакте: {self.bot_session.api_version}."
                )

        # Инициализация дополнительных переменных
        self.event = {}
        self.admins = os.environ["ADMINS_IDS"].split(",")

        # Переименование обрабатываемых типов событий
        self.NEW_MESSAGE = VkBotEventType.MESSAGE_NEW

        self.log.log.info(
            f"Беседа... {'Тестовая' if self.cid.endswith('1') else 'Основная'}"
        )

        self.log.log.info("Инициализация завершена.")

    def send_message(
        self,
        msg: str,
        pid: int = None,
        keyboard: str = "",
        attachments: str = None,
        user_ids: str = None,
        forward: str = "",
    ) -> NoReturn:

        """
        Отправка сообщения msg пользователю/в беседу pid
        с клавиатурой keyboard (не отправляется, если не указан json файл)
        """

        try:
            self.bot_vk.messages.send(
                peer_id=pid,
                random_id=random.getrandbits(64),
                message=msg,
                keyboard=keyboard,
                attachments=attachments,
                user_ids=user_ids,
                forward_messages=forward,
            )

        except vk_api.exceptions.ApiError as e:
            self.log.log.error(msg=e.__str__())
        except FileNotFoundError as e:
            self.log.log.error(msg=e)

    def send_mailing(self, ids: str, msg: str = "") -> NoReturn:
        """
        Отправка рассылки
        """
        self.send_message(msg=msg, user_ids=ids)

    def _get_users_info(self, ids: list) -> List[dict]:
        """
        Получает информацию о пользователях с указанными id
        """
        return self.bot_vk.users.get(user_ids=",".join(map(str, ids)))

    def generate_mentions(self, ids: str, names: bool) -> str:
        """
        Генерирует строку с упоминаниями из списка идентификаторов
        """
        if ids is not None:
            ids = list(filter(bool, ids.replace(" ", "").split(",")))
            users_info = self._get_users_info(ids)
            users_names = [
                users_info[i]["first_name"] if names else "!" for i in range(len(ids))
            ]
            result = (", " if names else "").join(
                [f"[id{_id}|{users_names[i]}]" for (i, _id) in enumerate(ids)]
            )
            return result
        return ""

    def current_is_admin(self) -> bool:
        """
        Проверяет, является ли текущий пользователь администратором бота
        """
        return str(self.event.object.from_id) in self.admins

    def send_gui(self, text: str = "Привет!") -> NoReturn:
        """
        Отправляет клавиатуру в зависимости от статуса пользователя
        """
        self.send_message(
            msg=text,
            pid=self.event.object.from_id,
            keyboard=self.kbs.generate_main_menu(self.current_is_admin()),
        )

    def update_version(self):
        """
        Обновляет версию в статусе группы с ботом
        """
        self.log.log.info("Обновление версии в статусе группы...")
        try:
            with open("VERSION.txt", "r") as f:
                v = f"Версия: {f.read()}"
            self.user_vk.status.set(text=v, group_id=self.gid)
        except vk_api.exceptions.ApiError as e:
            self.log.log.error(f"Ошибка {e.__str__()}")
        else:
            self.log.log.info(f"Успех.")
