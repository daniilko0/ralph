from urllib import parse as urlparse

import psycopg2


class Database:
    """
    Класс, описывающий методы для работы с базой данных PostgreSQL
    """

    def __init__(self, db_url):
        """
        Подключение к базе данных по её URL
        """
        url = urlparse.urlparse(db_url)
        self.db_auth = {
            "user": url.username,
            "password": url.password,
            "host": url.hostname,
            "port": url.port,
            "database": url.path[1:],
        }
        self.conn, self.cur = None, None

    def create_table(self, name, table: dict):
        """
        Создание новой таблицы
        """
        columns = [f"{column} {_type}" for column, _type in list(table.items())]
        self.query(f"CREATE TABLE {name} ({', '.join(columns)})")

    def query(self, query: str, args=None, fetchone=False, fetchall=False):
        """
        Обработка SQL - запроса
        """
        commit_func = ["create", "insert", "delete", "update"]
        result_func = ["select", "returning"]
        self.cur.execute(query, args) if args else self.cur.execute(query)

        if any(func in query.lower() for func in commit_func):
            self.commit()

        if any(func in query.lower() for func in result_func):
            if not fetchone and not fetchall:
                fetchall = True
        else:
            fetchone, fetchall = None, None

        if fetchone:
            exec_result = self.cur.fetchone()
        elif fetchall:
            exec_result = self.cur.fetchall()
        else:
            exec_result = None

        if fetchone or fetchall:
            return exec_result

    def commit(self):
        """
        Коммит изменений в БД
        """
        self.conn.commit()

    def data(self):
        """
        Возвращение указателя на БД
        """
        return self.cur

    def connect(self):
        """
        Переподключение к БД
        """
        self.conn = psycopg2.connect(**self.db_auth)
        self.cur = self.conn.cursor()

    def close(self):
        """
        Закрытие подключения к БД
        """
        self.cur.close()
        self.conn.close()
