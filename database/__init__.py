from itertools import groupby

from database.base import Base


class Database(Base):
    """
        Класс для методов работы с БД, выполняющих конечную цель
    """

    def get_last_names_letters(self):
        """
        Получает из базы данных все уникальные первые буквы фамилий
        """
        p = self.query("SELECT second_name FROM users_info")
        names = []
        for i, v in enumerate(p):
            names.append(v[0][0])
        names = [el for el, _ in groupby(names)]
        return names
