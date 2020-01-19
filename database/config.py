tables = dict()

tables["users"] = {
    "id": "serial PRIMARY KEY",
    "vk_id": "BIGINT NOT NULL CHECK (vk_id > 0) UNIQUE",
    "tg_id": "BIGINT CHECK (tg_id > 0) UNIQUE"
}


tables["users_info"] = {
    "user_id": "INTEGER NOT NULL PRIMARY KEY",

    "first_name": "VARCHAR (50) NOT NULL",
    "second_name": "VARCHAR (50) NOT NULL",

    "group_num": "SMALLINT NOT NULL CHECK (group_num > 0)",
    "subgroup_num": "SMALLINT NOT NULL CHECK (subgroup_num > 0)",
    "academic_status": "SMALLINT NOT NULL"
}

tables["sessions"] = {
    "id": "serial",
    "user_id": "INTEGER NOT NULL",
    "state": "INTEGER DEFAULT 0",
    "social": "SMALLINT DEFAULT 0",
    "PRIMARY KEY": "(user_id, social)"
}

tables["users_list"] = {
    "session_id": "INTEGER NOT NULL",
    "user_id": "INTEGER NOT NULL",
    "UNIQUE": "(session_id, user_id)"
}

tables["texts"] = {
    "session_id": "INTEGER NOT NULL PRIMARY KEY",
    "text": "VARCHAR (255) NOT NULL",
}