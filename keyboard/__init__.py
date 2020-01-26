import os

from vk_api.keyboard import VkKeyboard

from database import Database


class Keyboards:
    """
    Класс с генераторами пользовательских клавиатур
    """

    def __init__(self):
        self.db = Database(os.environ["DATABASE_URL"])

    def generate_alphabet_keyboard(self):
        """
        Генерирует клавиатуру с алфавитными кнопками для меню Призыва
        """
        kb = VkKeyboard()
        letters = self.db.get_last_names_letters()
        for i, v in enumerate(letters):
            if len(kb.lines[-1]) < 4:
                kb.add_button(label=v, payload={"button": "letter", "letter": v})
            else:
                kb.add_line()
        kb.add_line()
        kb.add_button(label="Отмена", color="negative", payload={"button": "cancel"})
        kb.add_button(label="Сохранить", color="positive", payload={"button": "save"})
        kb.add_line()
        kb.add_button(
            label="Отправить всем", color="primary", payload={"button": "send_to_all"}
        )
        return kb.get_keyboard()

    def generate_names_keyboard(self, letter):
        """
        Генерирует клавиатуру с фамилиями, начинающимися на букву (аргумент)
        """
        names = self.db.get_list_of_names(letter=letter)
        kb = VkKeyboard()
        for i, v in enumerate(names):
            label = f"{v[2]} {v[1][0]}."
            kb.add_button(
                label=label, payload={"button": "student", "name": label, "id": v[0]},
            )
            if len(kb.lines[-1]) == 2:
                kb.add_line()
        if kb.lines[-1]:
            kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "back"},
        )
        return kb.get_keyboard()
    
    def generate_list_of_mailings(self):
        mailings = self.db.get_mailings_list()
        kb = VkKeyboard()
        for i, v in enumerate(mailings):
            kb.add_button(
                label=v[1], payload={"button": "mailing", "id": v[0]},
            )
            if len(kb.lines[-1]) == 2:
                kb.add_line()
        if kb.lines[-1]:
            kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "home"},
        )
        return kb.get_keyboard()
