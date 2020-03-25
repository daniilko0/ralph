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
        vk_ids = [str(self.get_vk_id(_id)) for (_id,) in ids]
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

    def get_user_name(self, _id: int) -> str:
        """
        Получает из базы данных имя по идентификатор студента
        """
        name = self.query(f"SELECT first_name FROM users_info WHERE user_id={_id}")[0][
            0
        ]
        return name

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
        self.query(f"UPDATE texts SET attach=NULL WHERE session_id={s_id}")

    def empty_mailing_storage(self, user_id: int) -> NoReturn:
        """
        Очистить хранилище рассылок (выбранную рассылку и текст рассылки)
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE mailing_mgmt SET mailing=NULL WHERE session_id={s_id}")
        self.query(f"UPDATE mailing_mgmt SET m_text=NULL WHERE session_id={s_id}")
        self.query(f"UPDATE mailing_mgmt SET m_attach=NULL WHERE session_id={s_id}")

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

    def get_names_using_status(self, user_id: int) -> bool:
        """
        Получает статус использования имён
        """
        s_id = self.get_session_id(user_id)
        names_using = self.query(f"SELECT names_using FROM sessions WHERE id={s_id}")[
            0
        ][0]
        return bool(names_using)

    def update_names_using_status(self, user_id: int, value: int):
        """
        Изменяет статус использования имён
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE sessions SET names_using={value} WHERE id={s_id}")

    def get_users_names(self, ids: list) -> List[str]:
        """
        Получает список имён по списку идентификаторов ВКонтакте
        """
        ids = ", ".join(ids)
        query = self.query(
            f"SELECT first_name FROM users INNER JOIN users_info ON users.id = "
            f"users_info.user_id WHERE vk_id in ({ids}) ORDER BY "
            f"position(vk_id::text in '{ids}')"
        )
        names = [i for (i,) in query]
        return names

    def get_call_attaches(self, user_id: int):
        """Получает список вложений для сообщения с призывом
        """
        s_id = self.get_session_id(user_id)
        query = self.query(f"SELECT attach FROM texts WHERE session_id={s_id}")
        return query[0][0]

    def update_call_attaches(self, user_id: int, attach: str):
        """Обновляет список вложений для сообщения с призывом
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE texts SET attach='{attach}' WHERE session_id={s_id}")

    def get_mailing_attaches(self, user_id: int):
        """Получает список вложений для сообщения рассылки
        """
        s_id = self.get_session_id(user_id)
        query = self.query(f"SELECT m_attach FROM mailing_mgmt WHERE session_id={s_id}")
        return query[0][0]

    def update_mailing_attaches(self, user_id: int, attach: str):
        """Обновляет список вложений для сообщения рассылки
        """
        s_id = self.get_session_id(user_id)
        self.query(
            f"UPDATE mailing_mgmt SET m_attach='{attach}' WHERE session_id={s_id}"
        )

    def get_list_of_finances_categories(self) -> List[Tuple]:
        """Получает список доступных категорий расходов
        """
        query = self.query("SELECT name, slug FROM finances_categories")
        return query

    def add_expences_category(self, name: str, slug: str, s: int):
        query = self.query(
            f"INSERT INTO finances_categories (name, slug, sum) VALUES ('{name}', "
            f"'{slug}', {s}) RETURNING id"
        )

        return query[0][0]

    def get_active_expenses_category(self, user_id: int):
        """Получает текущую выбранную пользователем статью расходов
        """
        s_id = self.get_session_id(user_id)
        query = self.query(f"SELECT fin_cat FROM sessions WHERE id={s_id}")
        return query[0][0]

    def update_active_expenses_category(self, user_id: int, cat: str):
        """Обновляет текущую выбранную пользователем статью расходов
        """
        s_id = self.get_session_id(user_id)
        self.query(f"UPDATE sessions SET fin_cat='{cat}' WHERE id={s_id}")

    def add_expense(self, slug: str, summ: int):
        self.query(
            f"INSERT INTO finances_expenses (category, sum) VALUES ('{slug}', {summ})"
        )

    def get_expense_category_by_slug(self, slug: str) -> int:
        query = self.query(f"SELECT name FROM finances_categories WHERE slug='{slug}'")
        return query[0][0]

    def update_expense_summ(self, slug: str, summ: int):
        self.query(f"UPDATE finances_categories SET sum={summ} WHERE slug='{slug}'")

    def update_expense_name(self, slug: str, name: str):
        self.query(f"UPDATE finances_categories SET name='{name}' WHERE slug='{slug}'")

    def delete_expense_catgory(self, slug: str):
        self.query(f"DELETE FROM finances_categories WHERE slug='{slug}'")

    def get_all_donates_in_category(self, slug: str):
        query = self.query(f"SELECT sum FROM finances_donates WHERE slug='{slug}'")
        return [i for (i,) in query]

    def get_all_donates(self):
        query = self.query(f"SELECT sum FROM finances_donates")
        return [i for (i,) in query]

    def get_all_expenses_in_category(self, slug: str):
        query = self.query(f"SELECT sum FROM finances_expenses WHERE slug='{slug}'")
        return [i for (i,) in query]

    def get_all_expenses(self):
        query = self.query(f"SELECT sum FROM finances_expenses")
        return [i for (i,) in query]

    def get_expense_summ(self, slug: str):
        query = self.query(f"SELECT sum FROM finances_categories WHERE slug='{slug}'")
        return query[0][0]

    def create_donate(self, s_id: int, slug: str, summ: int):
        self.query(
            f"INSERT INTO finances_donates (student_id, category, sum) VALUES ({s_id}, "
            f"'{slug}', {summ})"
        )

    def get_list_of_donaters_by_slug(self, slug: str):
        query = self.query(
            f"SELECT student_id FROM finances_donates WHERE category='{slug}'"
        )
        return [i for (i,) in query]
