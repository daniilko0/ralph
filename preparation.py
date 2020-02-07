import os

import psycopg2.errors

from database import Database
from database.config import tables


def generate_tables(db):
    for (name, table) in tables.items():
        if not db.find_table(name):
            try:
                db.create_table(name, table)
                print(f"Таблица {name} создана.", end="\n\n")
            except psycopg2.errors.SyntaxError as error:
                print(f"Неудача. В описании таблицы {name} допущены ошибки.\n{error}")
                return
        else:
            print(f"Таблица {name} уже существует.", end="\n\n")


def migrations_6_1_0(db):
    print("start of migration")
    data = db.query("SELECT * FROM students")
    for (
        _____,
        first_name,
        second_name,
        _,
        group_num,
        subgroup_num,
        vk_id,
        __,
        ___,
        academic_status,
        ____,
    ) in data:
        (user_id,) = db.query(
            f"INSERT INTO users (vk_id) VALUES ({vk_id}) RETURNING id", fetchone=True
        )
        db.query(
            f"INSERT INTO users_info (user_id, first_name, second_name, group_num, subgroup_num, academic_status) VALUES ({user_id}, '{first_name}', '{second_name}', {group_num}, {subgroup_num}, {academic_status})"
        )
    print("end of migration")


if __name__ == "__main__":
    db = Database(os.environ["DATABASE_URL"], logs=False)
    generate_tables(db)
    migrations_6_1_0(db)
    db.close()
