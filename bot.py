"""
:project: ralph
:version: see VERSION.txt
:authors: dadyarri, 6a16ec
:contact: https://vk.me/dadyarri, https://vk.me/6a16ec
:license: MIT

:copyright: (c) 2019 - 2020 dadyarri, 6a16ec

"""


import os
import random
from typing import List
from typing import NoReturn

import requests
import vk_api

from database import Database
from keyboard import Keyboards
import logger
from vkbotlongpoll import RalphVkBotLongPoll
from singleton import SingletonMeta


class Bot(metaclass=SingletonMeta):
    """Класс, описывающий объект бота, включая авторизацию в API, и все методы бота.
    
    Attributes:
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
            bot.auth()
    """

    def __init__(self) -> None:

        self.log = logger.init_logger()

        self.log.info("Инициализация...")

        self.token = os.environ["VK_TOKEN"]
        self.user_token = os.environ["VK_USER_TOKEN"]
        self.gid = os.environ["GID_ID"]
        self.cid = os.environ["CID_ID"]

        self.kbs = Keyboards()

        self.db = Database(os.environ["DATABASE_URL"])
        self.admins = os.environ["ADMINS_IDS"].split(",")

        self.bot_session = None
        self.user_session = None
        self.bot_vk = None
        self.user_vk = None
        self.longpoll = None

        self.log.info(
            f"Беседа..." f" {'Тестовая' if self.cid.endswith('1') else 'Основная'}"
        )

        self.log.info("Инициализация завершена.")

    def auth(self):

        """Авторизация ВКонтакте, подключение к API
        """

        self.log.info("Авторизация ВКонтакте...")
        try:
            self.bot_session = vk_api.VkApi(token=self.token, api_version="5.103")
            self.user_session = vk_api.VkApi(token=self.user_token, api_version="5.103")
            self.bot_vk = self.bot_session.get_api()
            self.user_vk = self.user_session.get_api()
            self.longpoll = RalphVkBotLongPoll(vk=self.bot_session, group_id=self.gid)
        except vk_api.exceptions.AuthError:
            self.log.exception("Авторизация ВКонтакте неудачна. Ошибка авторизации.")
        except requests.exceptions.ConnectionError:
            self.log.exception(
                "Авторизация ВКонтакте неудачна. Превышен лимит попыток подключения."
            )
        except vk_api.exceptions.ApiError:
            self.log.exception("Авторизация ВКонтакте неудачна. Ошибка доступа.")
        else:
            self.log.info("Авторизация ВКонтакте успешна.")

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
            self.log.exception(msg=e.__str__())

    def generate_mentions(self, ids: str, names: bool) -> str:
        """Генерирует строку с упоминаниями из списка идентификаторов
        
        Arguments:
            ids: Перечень идентификаторов пользователей
            names: Флаг, указывающий на необходимость использования имён
            
        Returns:
            str: Сообщение, упоминающее выбранных пользователей
        """
        ids = ids.replace(" ", "").split(",")[:-1]
        if names:
            users_names = self.db.get_users_names(ids)
        else:
            users_names = ["!"] * len(ids)
        result = (", " if names else "").join(
            [f"@id{_id}({users_names[i]})" for (i, _id) in enumerate(ids)]
        )
        return result

    def is_admin(self, _id: int) -> bool:
        """Проверяет, является ли пользователь администратором бота

        Arguments:
            _id: Идентификатор пользователя для проверки привелегий
        Returns:
            bool: Флаг, указывающий на принадлежность текущего пользователя к касте Администраторов
        """
        return str(_id) in self.admins

    def send_gui(self, pid: int, text: str = "Привет!") -> NoReturn:
        """Отправляет клавиатуру главного меню
        
        Arguments:
            pid: Получатель клавиатуры
            text: Сообщение, вместе с которым будет отправлена клавиатура
        """
        self.send_message(
            msg=text, pid=pid, keyboard=self.kbs.generate_main_menu(self.is_admin(pid)),
        )

    def update_version(self):
        """
        Обновляет версию в статусе группы с ботом
        """

        self.log.info("Обновление версии в статусе группы...")
        try:
            with open("VERSION.txt", "r") as f:
                v = f"Версия: {f.read()}"
            self.user_vk.status.set(text=v, group_id=self.gid)
        except vk_api.exceptions.ApiError as e:
            self.log.error(f"Ошибка {e.__str__()}")
        else:
            self.log.info(f"Статус группы успешно обновлён.")
