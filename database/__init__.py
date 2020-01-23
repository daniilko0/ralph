from database.base import Base


class Database(Base):
    """
        Класс для методов работы с БД, выполняющих конечную цель
    """

    def get_last_names_letters(self):
        """
        Получает из базы данных все уникальные первые буквы фамилий
        """
        r = self.query("SELECT second_name FROM users_info")
        names = []
        for i, v in enumerate(r):
            if not v[0][0] in names:
                names.append(v[0][0])
        return names

    def get_list_of_names(self, letter):
        """
        Получает из базы данных все фамилии, начинающиеся на букву
        """
        r = self.query(
            "SELECT user_id, first_name, second_name FROM users_info WHERE "
            "substring(second_name from '^.') = %s AND academic_status > 0",
            (letter,),
        )
        return r
