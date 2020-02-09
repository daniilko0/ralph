tables = dict()

tables["calls"] = {"seesion_id": "integer", "ids": "varchar(400)"}

tables["mailing_mgmt"] = {
    "session_id": "integer",
    "mailing": "varchar(50)",
    "m_text": "varchar(1000)",
}

tables["mailings"] = {
    "mailing_id": "serial integer",
    "mailing_name": "varchar(70)",
    "mailing_slug": "varchar(30)",
}

tables["sessions"] = {
    "id": "serial integer",
    "vk_id": "integer",
    "state": "varchar(35)",
    "conversation": "integer default 2000000001",
}

tables["texts"] = {
    "session_id": "integer",
    "text": "varchar(1200)",
}

tables["users"] = {
    "id": "serial PRIMARY KEY",
    "vk_id": "BIGINT NOT NULL CHECK (vk_id > 0) UNIQUE",
    "tg_id": "BIGINT CHECK (tg_id > 0) UNIQUE",
}

tables["users_info"] = {
    "user_id": "INTEGER NOT NULL PRIMARY KEY",
    "first_name": "VARCHAR (50) NOT NULL",
    "second_name": "VARCHAR (50) NOT NULL",
    "group_num": "SMALLINT NOT NULL CHECK (group_num > 0)",
    "subgroup_num": "SMALLINT NOT NULL CHECK (subgroup_num > 0)",
    "academic_status": "SMALLINT NOT NULL",
}

tables["vk_subscriptions"] = {
    "user_id": "serial integer",
    "common": "smallint default 1",
    "schedule": "smallint default 1",
    "updates": "smallint default 0",
}
