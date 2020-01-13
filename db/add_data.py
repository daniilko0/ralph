import os

from db import Database

db = Database(os.environ["DATABASE_URL"])
db.connect()

with open("students.txt", "r", encoding="UTF-8") as st:
    for i in st.readlines():
        item = ", ".join(i.replace("\n", "").split(":"))
        a = (
            f"INSERT into students (vk_id, first_name, surname, group_number, "
            "subgroup_number, status, is_admin) VALUES ({item})"
        )
        db.query(a)
