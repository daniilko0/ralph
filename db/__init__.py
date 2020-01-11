import urllib.parse as urlparse

import psycopg2


class Database:
    def __init__(self, db_url):
        url = urlparse.urlparse(db_url)
        self.db_auth = {
            "user": url.username,
            "password": url.password,
            "host": url.hostname,
            "port": url.port,
            "database": url.path[1:]
            # "dbname": url.path[1:]
        }
        self.conn, self.cur = None, None
        self.fetchone, self.fetchall, self.one_query = False, False, False

    def create_table(self, name, table: dict):
        columns = ["%s %s" % (column, type) for column, type in list(table.items())]
        # print(columns)
        self.query(f"CREATE TABLE {name} ({', '.join(columns)})")

    def query(self, query: str, args=None, fetchone=False, fetchall=False):
        self.fetchone = True if fetchone == True else self.fetchone
        self.fetchall = True if fetchall == True else self.fetchall
        self.cur.execute(query, args) if args else self.cur.execute(query)

        commit_func = ["create", "insert", "delete", "update"]
        if any(func in query.lower() for func in commit_func):
            need_commit = True
        else:
            need_commit = False
        self.commit() if need_commit else None

        result_func = ["select", "returning"]
        if any(func in query.lower() for func in result_func):
            fetch_one, fetch_all = self.fetchone, self.fetchall
            if not fetch_one and not fetch_all:
                fetch_all = True
        else:
            fetch_one, fetch_all = None, None

        exec_result = self.cur.fetchone() if fetch_one \
            else self.cur.fetchall() if fetch_all \
            else None

        self.close() if self.one_query else None

        if fetch_one or fetch_all:
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
