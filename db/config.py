tables = dict()

tables["students"] = {
    "user_id": "serial PRIMARY KEY",
    "first_name": "VARCHAR (50) NOT NULL",
    "surname": "VARCHAR (50) NOT NULL",
    "patronymic": "VARCHAR (50)",
    "group_number": "SMALLINT NOT NULL CHECK (group_number > 0)",
    "subgroup_number": "SMALLINT CHECK (subgroup_number > 0)",
    "vk_id": "BIGINT NOT NULL CHECK (vk_id > 0)",
    "tg_id": "BIGINT CHECK (tg_id > 0)",
    "email": "VARCHAR (355) UNIQUE",
    "status": "SMALLINT DEFAULT 1 CHECK (1 <= status), CHECK (status <= 5)",
    "is_admin": "SMALLINT DEFAULT 0"
}