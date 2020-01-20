import urllib.parse as urlparse

import psycopg2


class Base:
    def __init__(self, db_url, logs=False):
        self.logs = logs
        url = urlparse.urlparse(db_url)
        self.db_auth = {
            "user": url.username,
            "password": url.password,
            "host": url.hostname,
            "port": url.port,
            "database": url.path[1:],
        }
        self.conn, self.cur = None, None
        self.connect()

    def create_table(self, name, table: dict):
        columns = [f"{column} {_type}" for column, _type in list(table.items())]
        self.query(f"CREATE TABLE {name} ({', '.join(columns)}) ")

    def find_table(self, name):
        res = self.query(
            f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='{name}'"
        )
        return len(res) > 0

    def query(self, query: str, args=None, fetchone=False, fetchall=False):
        print(query) if self.logs else None
        commit_func = ["create", "insert", "delete", "update"]
        result_func = ["select", "returning"]
        self.cur.execute(query, args) if args else self.cur.execute(query)

        if any(func in query.lower() for func in commit_func):
            self.commit()

        if any(func in query.lower() for func in result_func):
            if not fetchone and not fetchall:
                fetchall = True

        if fetchone:
            exec_result = self.cur.fetchone()
        elif fetchall:
            exec_result = self.cur.fetchall()
        else:
            exec_result = None

        if fetchone or fetchall:
            return exec_result

    def commit(self):
        self.conn.commit()

    def data(self):
        return self.cur

    def connect(self):
        self.conn = psycopg2.connect(**self.db_auth)
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()
