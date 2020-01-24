from database.base import Base


class Database(Base):
    """
        Класс для методов работы с БД, выполняющих конечную цель
    """

    def get_last_names_letters(self):
        """
        Получает из базы данных все уникальные первые буквы фамилий
        """
        r = self.query(
            "SELECT DISTINCT substring(second_name from  '^.') FROM users_info "
            "ORDER BY substring(second_name from  '^.')"
        )
        names = []
        for (item, ) in r:
            names.append(item)
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

    def get_vk_id(self, _id):
        r = self.query(f"SELECT vk_id from users WHERE id={_id}")[0][0]
        print(r)
