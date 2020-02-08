from typing import List
from typing import NoReturn
from typing import Tuple
from typing import Union

from database.base import Base

"""
Модуль, содержащий класс с методами для работы с БД, выполняющих конечную цель
"""


class Database(Base):
    """
        Класс для методов работы с БД, выполняющих конечную цель
    """

    def get_active_students_ids(self) -> list:
        ids = self.query(
            f"SELECT user_id FROM users_info WHERE academic_status > 0 ORDER BY user_id"
        )
        vk_ids = [self.get_vk_id(_id) for _id in ids]
        return vk_ids

    def get_last_names_letters(self) -> List[str]:
        """
        Получает из базы данных все уникальные первые буквы фамилий
        """
        letters = self.query(
            "SELECT DISTINCT substring(second_name from  '^.') FROM users_info "
            "ORDER BY substring(second_name from  '^.')"
        )
        return [letter for (letter,) in letters]

    def get_list_of_names(self, letter: str) -> List[Tuple]:
        """
        Получает из базы данных все фамилии, начинающиеся на букву
        """
        names = self.query(
            f"SELECT user_id, first_name, second_name FROM users_info "
            f"WHERE substring(second_name from '^.') = '{letter}' "
            f"AND academic_status > 0 ORDER BY user_id"
        )
        return names

    def get_vk_id(self, _id: Union[str, int]) -> int:
        """
        Получает из базы данных идентификатор ВКонтакте по идентификатору студента
        """
        vk_id = self.query(f"SELECT vk_id from users WHERE id={_id}")[0][0]
        return vk_id

    def get_user_id(self, vk_id: int) -> int:
        """
        Получает из базы данных идентификатор студента по идентификатору ВКонтакте
        """
        user_id = self.query(f"SELECT id from users WHERE vk_id={vk_id}")[0][0]
        return user_id

    def get_mailings_list(self) -> List[Tuple]:
        """
        Получает из базы данных весь список доступных рассылок
        """
        mailings = self.query(
            "SELECT mailing_id, mailing_name, mailing_slug from mailings"
        )
        return mailings

    def get_subscription_status(self, slug: str, user_id: int) -> int:
        """
        Получает статус подписки пользователя на рассылку
        """
        status = self.query(
            f"SELECT {slug} FROM vk_subscriptions WHERE user_id={user_id}"
        )[0][0]
        return status

    def is_user_exist(self, user_id: int) -> bool:
        """
        Возвращает информацию о том, существует ли пользователь в базе данных
        """
        user = self.query(f"SELECT id FROM users WHERE vk_id={user_id}")
        return bool(user)

    def is_session_exist(self, user_id: int) -> bool:
        """
        Проверяет существование сессии текущего пользователя
        """
        user = self.query(f"SELECT id FROM sessions WHERE vk_id={user_id}")
        return bool(user)

    def create_user(self, user_id: int) -> NoReturn:
        """
        Добавляет нового пользователя в таблицы информации и рассылок
        """
        self.query(f"INSERT INTO users (vk_id) VALUES ({user_id})")
        self.query(f"INSERT INTO vk_subscriptions DEFAULT VALUES")

    def create_session(self, user_id: int) -> NoReturn:
        """
        Создает новую сессию для пользователя
        """
        _id = self.query(f"SELECT id FROM users WHERE vk_id={user_id}")[0][0]
        self.query(
            f"INSERT INTO sessions (id, vk_id, state) VALUES ({_id}, {user_id}, 'main')"
        )

    def get_session_state(self, user_id: int) -> str:
        """
        Получает текущий статус бота из сессии
        """
        st = self.query(f"SELECT state FROM sessions WHERE vk_id={user_id}")
        return st[0][0]

    def get_session_id(self, user_id: int) -> int:
        """
        Получает идентификатор сессии
        """
        s_id = self.query(f"SELECT id FROM sessions WHERE vk_id={user_id}")[0][0]
        return s_id

    def update_session_state(self, user_id: int, state: str) -> NoReturn:
        """
        Изменяет текущий статус бота из сессии
        """
        self.query(f"UPDATE sessions SET state='{state}' WHERE vk_id={user_id}")

    def call_session_exist(self, user_id: int) -> bool:
        """
        Проверяет существование сессии призыва
        """
        s_id = self.get_session_id(user_id)
        call_exist = self.query(f"SELECT session_id FROM calls WHERE session_id={s_id}")
        texts_exist = self.query(
            f"SELECT session_id FROM texts WHERE session_id" f"={s_id}"
        )
        return bool(call_exist and texts_exist)

    def create_call_session(self, user_id: int) -> NoReturn:
        """
        Создает новую сессию призыва
        """
        s_id = self.get_session_id(user_id)
        self.query(f"INSERT INTO calls (session_id) VALUES ({s_id})")
        self.query(f"INSERT INTO texts (session_id) VALUES ({s_id})")

    def get_call_message(self, user_id: int) -> str:
        """
        Получает текст призыва
        """
        s_id = self.get_session_id(user_id)
        return self.query(f"SELECT text FROM texts WHERE session_id={s_id}")[0][0]

    def update_call_message(self, user_id: int, message: str) -> NoReturn:
        """
        Обновляет текст призыва
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE texts SET text='{message}' WHERE session_id={s_id}")

    def get_call_ids(self, user_id: int) -> str:
        """
        Получить список идентификаторов для призыва
        """
        s_id = self.get_session_id(user_id)
        ids = self.query(f"SELECT ids FROM calls WHERE session_id={s_id}")[0][0]
        return ids

    def update_call_ids(self, user_id: int, ids: str) -> NoReturn:
        """
        Перезаписать список идентификаторов для призыва
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE calls SET ids='{ids}' WHERE session_id={s_id}")

    def append_to_call_ids(self, user_id: int, _id: int) -> NoReturn:
        """
        Добавить идентификатор к списку для призыва
        """
        ids = self.get_call_ids(user_id)
        if ids is None:
            ids = ""
        ids += f"{_id},"
        self.update_call_ids(user_id, ids)

    def empty_call_storage(self, user_id: int) -> NoReturn:
        """
        Очистить хранилище призыва (текст призыва и список идентификатора)
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE calls SET ids=NULL WHERE session_id={s_id}")
        self.query(f"UPDATE texts SET text=NULL WHERE session_id={s_id}")

    def empty_mailing_storage(self, user_id: int) -> NoReturn:
        """
        Очистить хранилище рассылок (выбранную рассылку и текст рассылки)
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE mailing_mgmt SET mailing=NULL WHERE session_id={s_id}")
        self.query(f"UPDATE mailing_mgmt SET m_text=NULL WHERE session_id={s_id}")

    def get_mailing_message(self, user_id: int) -> str:
        """
        Получить текст рассылки
        """
        s_id = self.get_session_id(user_id)
        return self.query(f"SELECT m_text FROM mailing_mgmt WHERE session_id={s_id}")[
            0
        ][0]

    def update_mailing_message(self, user_id: int, message: str) -> NoReturn:
        """
        Перезаписывает текст рассылки
        """
        s_id = self.get_session_id(user_id)
        self.query(
            f"UPDATE mailing_mgmt SET m_text='{message}' WHERE session_id={s_id}"
        )

    def get_conversation(self, user_id: int) -> int:
        """
        Получает активную беседу
        """
        s_id = self.get_session_id(user_id)
        return self.query(f"SELECT conversation FROM sessions WHERE id={s_id}")[0][0]

    def update_conversation(self, user_id: int, conv_id: int) -> NoReturn:
        """
        Изменяет активную беседу
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE sessions SET conversation={conv_id} WHERE id" f"={s_id}")

    def mailing_session_exist(self, user_id: int) -> bool:
        """
        Проверяет наличие сессии рассылки
        """
        s_id = self.get_session_id(user_id)
        return self.query(
            f"SELECT session_id FROM mailing_mgmt WHERE session_id={s_id}"
        )

    def create_mailing_session(self, user_id: int) -> NoReturn:
        """
        Создает сессию рассылки
        """
        s_id = self.get_session_id(user_id)
        self.query(f"INSERT INTO mailing_mgmt (session_id) VALUES ({s_id})")

    def update_mailing_session(self, user_id: int, m_slug: str) -> NoReturn:
        """
        Изменяет выбранную рассылку
        """
        s_id = self.get_session_id(user_id)
        self.query(
            f"UPDATE mailing_mgmt SET mailing='{m_slug}' WHERE session_id={s_id}"
        )

    def get_mailing_session(self, user_id: int) -> str:
        """
        Получает выбранную рассылку
        """
        s_id = self.get_session_id(user_id)
        return self.query(f"SELECT mailing FROM mailing_mgmt WHERE session_id={s_id}")[
            0
        ][0]

    def fetch_subcribers(self, slug: str) -> str:
        """
        Собирает подписчиков рассылки
        """
        user_ids = self.query(f"SELECT user_id FROM vk_subscriptions WHERE {slug}=1")
        user_ids = [_id for (_id,) in user_ids]
        ids = []
        for i, _id in enumerate(user_ids):
            ids.append(self.query(f"SELECT vk_id FROM users WHERE id={_id}")[0][0])
        ids = ",".join(map(str, ids))
        return ids
