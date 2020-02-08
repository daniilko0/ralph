import os

import psycopg2.errors

from database import Database
from database.config import tables


def generate_tables(database):
    for (name, table) in tables.items():
        if not database.find_table(name):
            try:
                database.create_table(name, table)
                print(f"Table {name} created.")
            except psycopg2.errors.SyntaxError as error:
                print(f"Fail: {error}.")
                return
        else:
            print(f"Table {name} already exists.")


if __name__ == "__main__":
    db = Database(os.environ["DATABASE_URL"])
    generate_tables(db)
