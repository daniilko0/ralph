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

    def connect(self):
        self.conn = psycopg2.connect(**self.db_auth)
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()
