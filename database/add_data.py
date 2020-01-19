import os
from pprint import pprint

from database import Database


def return_str(itr):
    return f"'{itr}'"


if __name__ == "__main__":
    db = Database(os.environ["DATABASE_URL"])
    db.connect()

    cols = [
        "vk_id",
        "first_name",
        "surname",
        "group_number",
        "subgroup_number",
        "status",
        "is_admin",
    ]

    with open("students.txt", "r", encoding="UTF-8") as st:
        for i in st.readlines():
            item = ", ".join(map(return_str, i.split(":")))
            db.query(f"INSERT into students ({', '.join(cols)}) VALUES ({item})")

    pprint(db.query("SELECT * FROM students"))
    db.close()
