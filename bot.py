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
import warnings
from typing import List
from typing import NoReturn

import requests
import vk_api
from vk_api.bot_longpoll import VkBotEventType

from database import Database
from keyboard import Keyboards
from logger import Logger
from vkbotlongpoll import RalphVkBotLongPoll


class Bot:
    """Класс, описывающий объект бота, включая авторизацию в API, и все методы бота.
    
    Attributes:
        log (Logger): Объект класса Logger, содержащий настройки модуля logging
        token (str): Токен доступа к сообществу ВКонтакте
        user_token (str): Токен доступа пользователя-администратора ВКонтакте (используется для обновления статуса сообщества)
        gid (str): Идентификатор сообщества ВКонтакте
        cid (str): Идентификатор активной беседы (используется в рассылке расписания)
        kbs (Keyboards): Объект класса Keyboards, содержащий генераторы клавиатур
        db (Database): Объект класса Database, инициирующий подключение к базе данных
        admins (List[str]): Список идентификаторов ВКонтакте пользователей, имеющих доступ администратора бота 
    
    Example:
        .. code-block:: python
        
            from bot import Bot
        
            bot = Bot()
        
    Todo:
        * Почистить атрибуты
    """

    def __init__(self) -> None:

        self.log = Logger()

        self.log.log.info("Инициализация...")

        self.token = os.environ["VK_TOKEN"]
        self.user_token = os.environ["VK_USER_TOKEN"]
        self.gid = os.environ["GID_ID"]
        self.cid = os.environ["CID_ID"]

        self.kbs = Keyboards()

        self.db = Database(os.environ["DATABASE_URL"])

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

        """Обёртка над API ВКонтакте, отправляющая сообщения
        
        Arguments:
            msg: Текст отправляемого сообщения
            pid: Идентификатор пользователя/беседы/сообщества получателя сообщения (*не нужен, если указан user_ids*)
            keyboard: JSON-подобная строка со встроенной клавиатурой
            attachments: Вложения к сообщению (**не работает**)
            user_ids: Перечень адресатов для отправки одного сообщения (*не нужен, если указан pid*)
            forward: Перечень идентификаторов сообщений для пересылки
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
        """Отправка рассылки

        **Метод устарел!**
        
        Arguments:
            ids: Список идентификаторов пользователей-получателей рассылки
            msg: Сообщение рассылки
            
        Todo:
            Удалить и заменить на Bot.send_message
        
        """
        warnings.warn(
            message="Метод 'send_mailing' устарел, " "используйте 'send_message'",
            category=DeprecationWarning,
            stacklevel=2,
        )
        self.send_message(msg=msg, user_ids=ids)

    def get_users_names(self, ids: list) -> List[str]:
        """Получает имена пользователей  из базы данных по идентификаторам из списка
        
        Arguments:
            ids: Список идентификаторов для формирования списка имён
        
        Returns:
            List[str]: Список имён пользователей
        """
        user_ids = [
            self.db.query(f"SELECT id FROM users WHERE vk_id={i}")[0][0] for i in ids
        ]
        user_names = [
            self.db.query(f"SELECT first_name FROM users_info WHERE user_id={i}")[0][0]
            for i in user_ids
        ]
        return user_names

    def generate_mentions(self, ids: str, names: bool) -> str:
        """Генерирует строку с упоминаниями из списка идентификаторов
        
        Arguments:
            ids: Перечень идентификаторов пользователей
            names: Флаг, указывающий на необходимость использования имён
            
        Returns:
            str: Сообщение, упоминающее выбранных пользователей
        """
        ids = ids.split(",")
        if names:
            users_names = self.get_users_names(ids)
        else:
            users_names = ["!" for i in range(len(ids))]
        result = (", " if names else "").join(
            [f"@id{_id}({users_names[i]})" for (i, _id) in enumerate(ids)]
        )
        return result

    def current_is_admin(self) -> bool:
        """Проверяет, является ли текущий пользователь администратором бота
        
        Returns:
            bool: Флаг, указывающий на принадлежность текущего пользователя к касте Администраторов
            
        Todo:
            Сделать метод более общим
        """
        return str(self.event["message"]["from_id"]) in self.admins

    def send_gui(self, text: str = "Привет!") -> NoReturn:
        """Отправляет клавиатуру главного меню
        
        Arguments:
            text: Сообщение, вместе с которым будет отправлена клавиатура
        """
        self.send_message(
            msg=text,
            pid=self.event["message"]["from_id"],
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
