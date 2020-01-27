from database.base import Base


class Database(Base):
    """
        Класс для методов работы с БД, выполняющих конечную цель
    """

    def get_last_names_letters(self):
        """
        Получает из базы данных все уникальные первые буквы фамилий
        """
        letters = self.query(
            "SELECT DISTINCT substring(second_name from  '^.') FROM users_info "
            "ORDER BY substring(second_name from  '^.')"
        )
        return [letter for (letter,) in letters]

    def get_list_of_names(self, letter):
        """
        Получает из базы данных все фамилии, начинающиеся на букву
        """
        names = self.query(
            f"SELECT user_id, first_name, second_name FROM users_info "
            f"WHERE substring(second_name from '^.') = '{letter}' "
            f"AND academic_status > 0 ORDER BY user_id"
        )
        return names

    def get_vk_id(self, _id):
        """
        Получает из базы данных идентификатор ВКонтакте по идентификатору студента
        """
        vk_id = self.query(f"SELECT vk_id from users WHERE id={_id}")[0][0]
        return vk_id

    def get_user_id(self, vk_id):
        """
        Получает из базы данных идентификатор студента по идентификатору ВКонтакте
        """
        user_id = self.query(f"SELECT id from users WHERE vk_id={vk_id}")[0][0]
        return user_id

    def get_mailings_list(self):
        """
        Получает из базы данных весь список доступных рассылок
        """
        mailings = self.query(
            "SELECT mailing_id, mailing_name, mailing_slug from mailings"
        )
        return mailings
