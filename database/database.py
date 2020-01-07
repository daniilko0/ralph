import psycopg2
import urllib.parse as urlparse


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

        self.conn = psycopg2.connect()
        self.cur = self.conn.cursor()
