from typing import List
from typing import Tuple
from typing import Union

from psycopg2.extensions import AsIs

from database.base import Base

"""
Модуль, содержащий класс с методами для работы с БД, выполняющих конечную цель
"""


class Database(Base):
    """Класс для методов работы с БД, выполняющих конечную цель
    """

    def get_active_students_ids(self, group: int) -> list:
        """Получает список активных студентов (с любым статусом, кроме "отчислен")
        """
        ids = self.query(
            "SELECT user_id FROM users_info WHERE status_id > 0 AND group_num = %s ORDER BY "
            "user_id",
            (group,),
        )
        vk_ids = [str(self.get_vk_id(_id)) for (_id,) in ids]
        return vk_ids

    def get_last_names_letters(self, group: int) -> List[str]:
        """Получает из базы данных все уникальные первые буквы фамилий
        """
        letters = self.query(
            "SELECT DISTINCT substring(second_name from  '^.') FROM users_info where "
            "group_num = %s ORDER BY substring(second_name from  '^.')",
            (group,),
        )
        return [letter for (letter,) in letters]

    def get_list_of_names(self, letter: str, group: int) -> List[Tuple]:
        """Получает из базы данных все фамилии, начинающиеся на букву
        """
        names = self.query(
            "SELECT user_id, first_name, second_name FROM users_info "
            "WHERE substring(second_name from '^.') = %s "
            "AND status_id > 0 AND group_num = %s ORDER BY user_id",
            (letter, group),
        )
        return names

    def get_vk_id(self, _id: Union[str, int]) -> int:
        """Получает из базы данных идентификатор ВКонтакте по идентификатору студента
        """
        vk_id = self.query("SELECT vk_id from users WHERE id=%s", (_id,))
        return vk_id[0][0]

    def get_user_id(self, vk_id: int) -> int:
        """Получает из базы данных идентификатор студента по идентификатору ВКонтакте
        """
        user_id = self.query("SELECT id from users WHERE vk_id=%s", (vk_id,))
        return user_id[0][0]

    def get_user_name(self, _id: int) -> str:
        """Получает из базы данных имя по идентификатор студента
        """
        name = self.query("SELECT first_name FROM users_info WHERE user_id=%s", (_id,))
        return name[0][0]

    def get_mailings_list(self, group) -> List[Tuple]:
        """Получает из базы данных весь список доступных рассылок
        """
        mailings = self.query(
            "SELECT mailing_id, mailing_name from mailings where group_num=%s", (group,)
        )
        return mailings

    def get_subscription_status(self, m_id: int, user_id: int) -> int:
        """Получает статус подписки пользователя на рассылку
        """
        status = self.query(
            "SELECT status FROM subscriptions WHERE user_id=%s and mailing_id = %s",
            (user_id, m_id),
        )
        return status[0][0]

    def is_user_exist(self, user_id: int) -> bool:
        """Возвращает информацию о том, существует ли пользователь в базе данных
        """
        user = self.query("SELECT id FROM users WHERE vk_id=%s", (user_id,))
        return bool(user)

    def is_session_exist(self, user_id: int) -> bool:
        """Проверяет существование сессии текущего пользователя
        """
        user = self.query("SELECT id FROM sessions WHERE vk_id=%s", (user_id,))
        return bool(user)

    def create_user(self, user_id: int):
        """Добавляет нового пользователя в таблицы информации и рассылок
        """
        self.query("INSERT INTO users (vk_id) VALUES (%s)", (user_id,))

    def create_session(self, user_id: int):
        """Создает новую сессию для пользователя
        """
        _id = self.query("SELECT id FROM users WHERE vk_id=%s", (user_id,))[0][0]
        self.query(
            "INSERT INTO sessions (id, vk_id, state) VALUES (%s, %s, 'main')",
            (_id, user_id),
        )

    def get_session_state(self, user_id: int) -> str:
        """Получает текущий статус бота из сессии
        """
        st = self.query("SELECT state FROM sessions WHERE vk_id=%s", (user_id,))
        return st[0][0]

    def get_session_id(self, user_id: int) -> int:
        """Получает идентификатор сессии
        """
        s_id = self.query("SELECT id FROM sessions WHERE vk_id=%s", (user_id,))
        return s_id[0][0]

    def update_session_state(self, user_id: int, state: str):
        """Изменяет текущий статус бота из сессии
        """
        self.query("UPDATE sessions SET state = %s WHERE vk_id=%s", (state, user_id))

    def call_session_exist(self, user_id: int) -> bool:
        """Проверяет существование сессии призыва
        """
        s_id = self.get_session_id(user_id)
        call_exist = self.query(
            "SELECT session_id FROM calls WHERE session_id=%s", (s_id,)
        )
        texts_exist = self.query(
            "SELECT session_id FROM texts WHERE session_id=%s", (s_id,)
        )
        return bool(call_exist and texts_exist)

    def create_call_session(self, user_id: int):
        """Создает новую сессию призыва
        """
        s_id = self.get_session_id(user_id)
        self.query("INSERT INTO calls (session_id) VALUES (%s)", (s_id,))
        self.query("INSERT INTO texts (session_id) VALUES (%s)", (s_id,))

    def get_call_message(self, user_id: int) -> str:
        """Получает текст призыва
        """
        s_id = self.get_session_id(user_id)
        call_text = self.query("SELECT text FROM texts WHERE session_id=%s", (s_id,))
        return call_text[0][0]

    def update_call_message(self, user_id: int, message: str):
        """Обновляет текст призыва
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE texts SET text = %s WHERE session_id=%s", (message, s_id))

    def get_call_ids(self, user_id: int) -> str:
        """Получить список идентификаторов для призыва
        """
        s_id = self.get_session_id(user_id)
        ids = self.query("SELECT ids FROM calls WHERE session_id=%s", (s_id,))
        return ids[0][0]

    def update_call_ids(self, user_id: int, ids: str):
        """Перезаписать список идентификаторов для призыва
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE calls SET ids = %s WHERE session_id=%s", (ids, s_id))

    def append_to_call_ids(self, user_id: int, _id: int):
        """Добавить идентификатор к списку для призыва
        """
        ids = self.get_call_ids(user_id)
        if ids is None:
            ids = ""
        ids += f"{_id},"
        self.update_call_ids(user_id, ids)

    def update_subscribe_state(self, m_id: int, u_id: int, state: int):
        """Обновляет статус подписки на рассылку
        """
        self.query(
            "UPDATE subscriptions SET status = %s WHERE user_id=%s and mailing_id = %s",
            (state, u_id, m_id),
        )

    def empty_call_storage(self, user_id: int):
        """Очистить хранилище призыва (текст призыва и список идентификатора)
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE calls SET ids=NULL WHERE session_id=%s", (s_id,))
        self.query("UPDATE texts SET text=NULL WHERE session_id=%s", (s_id,))
        self.query("UPDATE texts SET attach=NULL WHERE session_id=%s", (s_id,))

    def empty_mailing_storage(self, user_id: int):
        """Очистить хранилище рассылок (выбранную рассылку и текст рассылки)
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE mailing_mgmt SET mailing=NULL WHERE session_id=%s", (s_id,))
        self.query("UPDATE mailing_mgmt SET m_text=NULL WHERE session_id=%s", (s_id,))
        self.query("UPDATE mailing_mgmt SET m_attach=NULL WHERE session_id=%s", (s_id,))

    def get_mailing_message(self, user_id: int) -> str:
        """Получить текст рассылки
        """
        s_id = self.get_session_id(user_id)
        m_message = self.query(
            "SELECT m_text FROM mailing_mgmt WHERE session_id=%s", (s_id,)
        )
        return m_message[0][0]

    def update_mailing_message(self, user_id: int, message: str):
        """Перезаписывает текст рассылки
        """
        s_id = self.get_session_id(user_id)
        self.query(
            "UPDATE mailing_mgmt SET m_text = %s WHERE session_id=%s", (message, s_id)
        )

    def get_conversation(self, user_id: int) -> int:
        """Получает активную беседу
        """
        s_id = self.get_session_id(user_id)
        conversation = self.query(
            "SELECT conversation FROM sessions WHERE id=%s", (s_id,)
        )
        return conversation[0][0]

    def update_conversation(self, user_id: int, conv_id: int):
        """Изменяет активную беседу
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE sessions SET conversation = %s WHERE id=%s", (conv_id, s_id))
        return conv_id

    def mailing_session_exist(self, user_id: int) -> bool:
        """Проверяет наличие сессии рассылки
        """
        s_id = self.get_session_id(user_id)
        session = self.query(
            "SELECT session_id FROM mailing_mgmt WHERE session_id=%s", (s_id,)
        )
        return bool(session)

    def create_mailing_session(self, user_id: int):
        """Создает сессию рассылки
        """
        s_id = self.get_session_id(user_id)
        self.query("INSERT INTO mailing_mgmt (session_id) VALUES (%s)", (s_id,))

    def update_mailing_session(self, user_id: int, m_slug: str):
        """Изменяет выбранную рассылку
        """
        s_id = self.get_session_id(user_id)
        self.query(
            "UPDATE mailing_mgmt SET mailing = %s WHERE session_id=%s", (m_slug, s_id)
        )

    def get_mailing_session(self, user_id: int) -> int:
        """Получает выбранную рассылку
        """
        s_id = self.get_session_id(user_id)
        mailing = self.query(
            "SELECT mailing FROM mailing_mgmt WHERE session_id=%s", (s_id,)
        )
        return mailing[0][0]

    def fetch_subcribers(self, m_id: int, group: int) -> str:
        """Собирает подписчиков рассылки
        """
        user_ids = self.query(
            "SELECT user_id FROM subscriptions WHERE status = 1 and mailing_id = %s",
            (m_id,),
        )
        user_ids = [_id for (_id,) in user_ids]
        ids = []
        for i, _id in enumerate(user_ids):
            ids.append(
                self.query(
                    "SELECT vk_id FROM users left outer join users_info on id = "
                    "user_id WHERE id=%s and group_num = %s",
                    (_id, group),
                )[0][0]
            )
        ids = ",".join(map(str, ids))
        return ids

    def get_names_using_status(self, user_id: int) -> bool:
        """Получает статус использования имён
        """
        s_id = self.get_session_id(user_id)
        names_using = self.query(
            "SELECT names_using FROM sessions WHERE id=%s", (s_id,)
        )
        return bool(names_using[0][0])

    def update_names_using_status(self, user_id: int, value: int):
        """Изменяет статус использования имён
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE sessions SET names_using = %s WHERE id=%s", (value, s_id))

    def get_users_names(self, ids: list) -> List[str]:
        """Получает список имён по списку идентификаторов ВКонтакте
        """
        ids = ", ".join(ids)
        query = self.query(
            "SELECT first_name FROM users INNER JOIN users_info ON "
            "users.id = users_info.user_id WHERE vk_id in (%s) ORDER "
            "BY position(vk_id::text in %s)",
            (AsIs(ids), ids),
        )
        names = [i for (i,) in query]
        return names

    def get_call_attaches(self, user_id: int):
        """Получает список вложений для сообщения с призывом
        """
        s_id = self.get_session_id(user_id)
        query = self.query("SELECT attach FROM texts WHERE session_id=%s", (s_id,))
        return query[0][0]

    def update_call_attaches(self, user_id: int, attach: str):
        """Обновляет список вложений для сообщения с призывом
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE texts SET attach = %s WHERE session_id=%s", (attach, s_id))

    def get_mailing_attaches(self, user_id: int):
        """Получает список вложений для сообщения рассылки
        """
        s_id = self.get_session_id(user_id)
        query = self.query(
            "SELECT m_attach FROM mailing_mgmt WHERE session_id=%s", (s_id,)
        )
        return query[0][0]

    def update_mailing_attaches(self, user_id: int, attach: str):
        """Обновляет список вложений для сообщения рассылки
        """
        s_id = self.get_session_id(user_id)
        self.query(
            "UPDATE mailing_mgmt SET m_attach = %s WHERE session_id=%s", (attach, s_id)
        )

    def get_list_of_finances_categories(self, group: int) -> List[Tuple]:
        """Получает список доступных категорий расходов
        """
        query = self.query(
            "SELECT id, name FROM finances_categories where group_num=%s", (group,)
        )
        return query

    def add_expences_category(self, name: str, s: int, group: int):
        """Созадет новую категорию расходов
        """
        query = self.query(
            "INSERT INTO finances_categories (name, sum, group_num) VALUES (%s, %s, %s) RETURNING id",
            (name, s, group),
        )

        return query[0][0]

    def get_active_expenses_category(self, user_id: int):
        """Получает текущую выбранную пользователем статью расходов
        """
        s_id = self.get_session_id(user_id)
        query = self.query("SELECT fin_cat FROM sessions WHERE id=%s", (s_id,))
        return query[0][0]

    def update_active_expenses_category(self, user_id: int, cat: str):
        """Обновляет текущую выбранную пользователем статью расходов
        """
        s_id = self.get_session_id(user_id)
        self.query("UPDATE sessions SET fin_cat = %s WHERE id = %s", (cat, s_id))

    def add_expense(self, e_id: int, summ: int):
        """Создает новый расход
        """
        self.query(
            "INSERT INTO finances_expenses (category, sum) VALUES (%s, %s)",
            (e_id, summ),
        )

    def get_expense_category_by_slug(self, cat_id: int) -> int:
        """Получет название категории расхода по ИД категории
        """
        query = self.query(
            "SELECT name FROM finances_categories WHERE id=%s", (cat_id,)
        )
        return query[0][0]

    def update_expense_summ(self, e_id: int, summ: int):
        """Обновляет сумму сборов категории расхода
        """
        self.query(
            "UPDATE finances_categories SET sum = %s WHERE id = %s", (summ, e_id)
        )

    def update_expense_name(self, e_id: int, name: str):
        """Обновляет имя категории расхода
        """
        self.query("UPDATE finances_categories SET name = %s WHERE id=%s", (name, e_id))

    def delete_expense_catgory(self, e_id: int):
        """Удаляет категорию расхода
        """
        self.query("DELETE FROM finances_categories WHERE id=%s", (e_id,))

    def get_all_donates_in_category(self, cat_id: int):
        """Получает сумму всех сборов по категории
        """
        query = self.query(
            "SELECT sum FROM finances_donates WHERE category=%s", (cat_id,)
        )
        return [i for (i,) in query]

    def get_all_donates(self):
        """Получает сумму всех сборов
        """
        query = self.query("SELECT sum FROM finances_donates")
        return [i for (i,) in query]

    def get_all_expenses_in_category(self, e_id: int):
        """Получает все расходы в категории
        """
        query = self.query(
            "SELECT sum FROM finances_expenses WHERE category=%s", (e_id,)
        )
        return [i for (i,) in query]

    def get_all_expenses(self):
        """Получает все расходы
        """
        query = self.query("SELECT sum FROM finances_expenses")
        return [i for (i,) in query]

    def get_expense_summ(self, e_id: int):
        """Получает сумму сбора категории
        """
        query = self.query("SELECT sum FROM finances_categories WHERE id=%s", (e_id,))
        return query[0][0]

    def create_donate(self, s_id: int, slug: str):
        """Создает новый взнос
        """
        query = self.query(
            "INSERT INTO finances_donates (student_id, category) VALUES (%s, %s) "
            "RETURNING id",
            (s_id, slug),
        )
        return query[0][0]

    def delete_donate(self, d_id: int):
        """Удаляет взнос
        """
        self.query("DELETE FROM finances_donates WHERE id=%s", (d_id,))

    def get_summ_of_donate(self, d_id: int):
        """Получает сумму взноса

        Args:
            d_id: Идентификатор взноса

        Returns:
            int: Сумма взноса
        """
        query = self.query("SELECT sum FROM finances_donates WHERE id=%s", (d_id,))
        return query[0][0]

    def append_summ_to_donate(self, d_id: int, summ: int):
        """Добавляет сумму к сбору
        """
        source = self.get_summ_of_donate(d_id)
        new = summ + source
        self.query("UPDATE finances_donates SET sum = %s WHERE id=%s", (new, d_id))

    def update_donate_id(self, u_id: int, d_id: int):
        """Обновляет иденифиткатор создаваемого взноса в хранилище
        """
        self.query("UPDATE sessions SET donate_id = %s WHERE vk_id=%s", (d_id, u_id))

    def get_donate_id(self, u_id: int):
        """Получет иденифиткатор создаваемого взноса в хранилище
        """
        query = self.query("SELECT donate_id FROM sessions WHERE vk_id=%s", (u_id,))
        return query[0][0]

    def get_list_of_donaters_by_slug(self, slug: str, summ: int = 0):
        """Получает список идентификаторов всех внесших деньги на определенную категорию
        """
        query = self.query(
            "SELECT student_id FROM finances_donates WHERE category=%s AND sum >= %s",
            (slug, summ),
        )
        return [i for (i,) in query]

    def get_id_of_donate_record(self, _id, slug) -> int:
        """Получает идентификатор записи взноса
        Args:
            _id: Идентификатор студента, внесшего деньги
            slug: Слаг категории расхода

        Returns:
            int: Идентификатор записи
        """
        query = self.query(
            "SELECT id FROM finances_donates WHERE student_id=%s AND category=%s",
            (_id, slug),
        )
        return query[0][0]

    def set_current_date_as_update(self, d_id):
        """Устанавливает текущую дату в качестве даты изменения записи о взносе
        Args:
            d_id: Иденитфикатор записи взноса

        """
        self.query(
            "UPDATE finances_donates SET updated_date = (SELECT CURRENT_DATE) WHERE id=%s",
            (d_id,),
        )

    def get_list_of_administrators(self):
        """Получает список администраторов бота
        """
        admins = self.query("select * from administrators")
        return admins

    def get_group_of_user(self, vk_id: int):
        """Получает номер группы студента по идентификатору ВК
        """
        user_id = self.get_user_id(vk_id)
        group = self.query(
            "select group_num from users_info where user_id=%s", (user_id,)
        )
        return group[0][0]

    def get_schedule_descriptor(self, g_id: int):
        """Получает дескриптор расписания

        Args:
            g_id: Номер группы

        Returns:
            str: Дескриптор расписания
        """
        desc = self.query(
            "select schedule_descriptor from schedule where group_num = %s", (g_id,)
        )
        return desc[0][0]

    def get_list_of_groups(self):
        """Получает список групп с описанием

        Returns:
            List[tuple]: Список созданных групп
        """
        groups = self.query("select * from groups")
        return groups

    def get_administrating_groups(self, admin_id: int):
        """Получает список групп доступных пользователю для администрирования

        Args:
            admin_id: Идентификатор пользователя
        Returns:
            List[int]: Список номеров групп
        """
        groups = self.query(
            "select group_num from administrators where vk_id=%s", (admin_id,)
        )
        return [i for (i,) in groups]

    def get_registered_chats(self):
        """Получает список зарегистрированных чатов"""
        chats = self.query("select chat_id from chats")
        return [chat for (chat,) in chats]

    def get_chats_of_group(self, group: int):
        """Получает список чатов, привязанных к группе

        Args:
            group: Номер группы
        Returns:
            List[Tuple[int, int]]: Список чатов
        """
        chats = self.query(
            "select chat_id, chat_type from chats where group_num=%s", (group,)
        )
        return chats

    def get_cached_chats(self):
        """Получает список сохраненных чатов"""
        chats = self.query("select chat_id from chat_cache")
        return [chat for (chat,) in chats]

    def add_cached_chat(self, chat_id: int):
        """Сохраняет чат в кеш
        Args:
            chat_id: Идентификатор чата для сохранения
        """
        self.query("insert into chat_cache (chat_id) values (%s)", (chat_id,))

    def remove_cached_chat(self, chat_id: int):
        """Удаляет чат из кеша
        Args:
            chat_id: Идентификатор чата для удаления
        """
        self.query("delete from chat_cache where chat_id=%s", (chat_id,))

    def is_main_chat_added(self, group: int):
        """Проверяет наличие добавленного основного чата в группу
        Args:
            group: Номер группы
        Returns:
            bool: Наличие основного чата
        """
        chat = self.query(
            "select chat_id from chats where group_num=%s and " "chat_type=%s",
            (group, 1),
        )
        return bool(chat)

    def is_test_chat_added(self, group: int):
        """Проверяет наличие добавленного тестового чата в группу
        Args:
            group: Номер группы
        Returns:
            bool: Наличие основного чата
        """
        chat = self.query(
            "select chat_id from chats where group_num=%s and " "chat_type=%s",
            (group, 0),
        )
        return bool(chat)

    def registrate_chat(self, chat_id: int, chat_type: int, group: int):
        """Регистрирует чат
        Args:
            chat_id: Идентификатор регистрируемого чата
            chat_type: Тип чата (0/1)
            group: Номер группы
        """
        self.query(
            "insert into chats (chat_id, chat_type, group_num) values (%s, %s, %s)",
            (chat_id, chat_type, group),
        )

    def is_chat_active(self, group: int, chat_type: int):
        """
        Возвращает статус чата (активен/не активен)
        Args:
            group: Номер группы
            chat_type: Тип чата (тестовый/основной)

        Returns:
            bool: Статус чата
        """
        chat_status = self.query(
            "select is_active from chats where group_num=%s and chat_type=%s",
            (group, chat_type),
            fetchone=True,
        )
        return bool(chat_status[0])

    def update_chat_activity(self, group: int, chat_type: int, new_state: int):
        """
        Изменяет статус активности чата
        Args:
            group: Номер группы
            chat_type: Тип чата (тестовый/основной)
            new_state: Новое состояние чата
        """
        self.query(
            "update chats set is_active = %s where group_num=%s and " "chat_type=%s",
            (new_state, group, chat_type),
        )

    def unpin_chat(self, group: int, chat_type: int):
        """
        Открепляет чат
        Args:
            group: Номер группы
            chat_type: Тип чата
        """
        self.query(
            "delete from chats where group_num=%s and chat_type=%s", (group, chat_type)
        )

    def get_active_chat_id(self, group: int):
        """
        Получает идентификатор акивного чата группы
        Args:
            group: Номер группы

        Returns:
            int: Идентфикатор чата
        """
        chat = self.query(
            "select chat_id from chats where chat_type=1 and " "group_num=%s",
            (group,),
            fetchone=True,
        )
        return chat[0]

    def get_chat_id(self, group: int, chat_type: int):
        """
        Получает идентификатор чата
        Args:
            group: Номер группы
            chat_type: Тип чата (тестовый/основной)

        Returns:
            int: Идентификатор чата
        """
        chat = self.query(
            "select chat_id from chats where chat_type=%s and group_num=%s",
            (chat_type, group),
            fetchone=True,
        )
        return chat[0]
