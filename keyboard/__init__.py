import os

from vk_api.keyboard import VkKeyboard

from database import Database


class Keyboards:
    """
    Класс с генераторами пользовательских клавиатур
    """

    def __init__(self):
        self.db = Database(os.environ["DATABASE_URL"])

    @staticmethod
    def generate_main_menu(is_admin: bool):
        """
        Генерирует клавиатуру с главным меню
        """
        kb = VkKeyboard()
        if is_admin:
            kb.add_button(label="Призыв", payload={"button": "call"})
            kb.add_line()
        kb.add_button(label="Расписание", payload={"button": "schedule"})
        kb.add_line()
        kb.add_button(
            label="Управление рассылками", payload={"button": "mailings"},
        )
        if is_admin:
            kb.add_line()
            kb.add_button(label="Настройки", payload={"button": "prefs"})
        return kb.get_keyboard()

    @staticmethod
    def generate_schedule_keyboard():
        """
        Возвращает клавиатуру с выбором даты получения расписания
        """
        kb = VkKeyboard()
        kb.add_button(label="На сегодня", color="default", payload={"button": "today"})
        kb.add_button(
            label="На завтра", color="default", payload={"button": "tomorrow"}
        )
        kb.add_line()
        kb.add_button(
            label="На послезавтра",
            color="default",
            payload={"button": "day_after_tomorrow"},
        )
        kb.add_button(
            label="Выбрать дату", color="default", payload={"button": "arbitrary"},
        )
        kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "home"},
        )
        return kb.get_keyboard()

    @staticmethod
    def empty():
        """
        Возвращает пустую клавиатуру
        """
        kb = VkKeyboard()
        return kb.get_empty_keyboard()

    @staticmethod
    def skip():
        """
        Возвращает клавиатуру с кнопкой "Пропустить"
        """
        kb = VkKeyboard()
        kb.add_button(label="Пропустить", payload={"button": "skip"})
        return kb.get_keyboard()

    @staticmethod
    def cancel():
        """
        Возвращает клавиатуру с кнопкой "Отмена"
        """
        kb = VkKeyboard()
        kb.add_button(label="Отмена", color="negative", payload={"button": "cancel"})
        return kb.get_keyboard()

    @staticmethod
    def generate_prefs_keyboard():
        """
        Возвращает клавиатуру с настройками бота
        """
        kb = VkKeyboard()
        kb.add_button(label="Сменить беседу", payload={"button": "chconv"})
        kb.add_line()
        kb.add_button(label="Использование имён в призыве", payload={"button": "names"})
        kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "home"},
        )
        return kb.get_keyboard()

    @staticmethod
    def generate_conv_selector(chat: int):
        """
        Возвращает клавиатуру-селектор бесед
        """
        kb = VkKeyboard()
        if chat == 2000000001:
            kb.add_button(
                label="Переключиться на основную беседу",
                payload={"button": "select_main_conv"},
            )
        elif chat == 2000000002:
            kb.add_button(
                label="Переключиться на тестовую беседу",
                payload={"button": "select_test_conv"},
            )
        kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "prefs"},
        )
        return kb.get_keyboard()

    @staticmethod
    def generate_names_selector(status: bool):
        kb = VkKeyboard()
        if status:
            kb.add_button(label="Выключить", payload={"button": "off_using_names"})
        else:
            kb.add_button(label="Включить", payload={"button": "on_using_names"})
        kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "prefs"},
        )
        return kb.get_keyboard()

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

    def generate_mailings_keyboard(self):
        """
        Генерация клавиатуры со списком доступных рассылок
        """
        mailings = self.db.get_mailings_list()
        kb = VkKeyboard()
        for i, v in enumerate(mailings):
            kb.add_button(
                label=v[1], payload={"button": "mailing", "name": v[1], "slug": v[2]},
            )
            if len(kb.lines[-1]) == 2:
                kb.add_line()
        if kb.lines[-1]:
            kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "home"},
        )
        return kb.get_keyboard()

    def generate_mailing_mgmt(self, user_id: int, is_admin: bool, slug: str):
        uid = self.db.get_user_id(vk_id=user_id)
        status = self.db.get_subscription_status(slug=slug, user_id=uid)

        kb = VkKeyboard()
        if is_admin:
            kb.add_button(
                label="Отправить рассылку",
                color="default",
                payload={"button": "send_mailing", "mailing": slug},
            )
        kb.add_button(
            label=f"{'Отписаться' if status else 'Подписаться'}",
            payload={
                "button": f"{'unsubscribe' if status else 'subscribe'}",
                "slug": slug,
                "user_id": uid,
            },
        )
        kb.add_line()
        kb.add_button(
            label="Назад", color="primary", payload={"button": "mailings"},
        )
        return kb.get_keyboard()

    def prompt(self, user_id: int = None):
        """
        Возвращает клавиатуру с подтверждением действия
        """
        kb = VkKeyboard()
        kb.add_button(
            label="Подтвердить", color="positive", payload={"button": "confirm"}
        )
        kb.add_button(label="Отмена", color="negative", payload={"button": "deny"})
        if (
            user_id is not None
            and self.db.get_session_state(user_id) == "call_configuring"
        ):
            kb.add_line()
            kb.add_button(
                label="Сменить беседу",
                color="primary",
                payload={"button": "chconv_call"},
            )
            kb.add_line()
            kb.add_button(
                label="Переключить использование имён",
                color="primary",
                payload={"button": "chnames_call"},
            )
        return kb.get_keyboard()
