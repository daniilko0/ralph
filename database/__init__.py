from database.base import Base


class Database(Base):
    def __init__(self, db_url, logs=False):
        super().__init__(db_url, logs)
