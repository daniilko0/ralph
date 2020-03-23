import datetime
import json
import os
import re
from enum import Enum

import requests
from vk_api.bot_longpoll import VkBotEventType
from googletrans import Translator

from bot import Bot
from database import Database
from keyboard import Keyboards
from scheduler import Date
from scheduler import Schedule

db = Database(os.environ["DATABASE_URL"])
bot = Bot()
kbs = Keyboards()

bot.auth()
bot.update_version()


class EventTypes(Enum):
    NEW_MESSAGE = VkBotEventType.MESSAGE_NEW


def generate_call_message():
    f = db.get_names_using_status(event["message"]["from_id"])
    students_ids = db.get_call_ids(event["message"]["from_id"])
    print(students_ids)
    if students_ids is not None:
        mentions = bot.generate_mentions(ids=students_ids, names=f)
    else:
        mentions = ""
    message = db.get_call_message(event["message"]["from_id"]) or ""
    message = f"{mentions}\n{message}"
    return message


def send_call_confirm():
    chat_id = int(str(db.get_conversation(event["message"]["from_id"]))[-1])
    message = generate_call_message()
    atch = db.get_call_attaches(event["message"]["from_id"])
    if atch is None:
        atch = ""
    if message != "\n" or atch:
        bot.send_message(
            msg=f"В {'тестовую ' if chat_id == 1 else 'основную '}"
            f"беседу будет отправлено сообщение:",
            pid=event["message"]["from_id"],
            keyboard=kbs.prompt(event["message"]["from_id"]),
        )
        bot.send_message(msg=message, pid=event["message"]["from_id"], attachment=atch)
    else:
        db.empty_call_storage(event["message"]["from_id"])
        bot.send_gui(
            pid=event["message"]["from_id"],
            text="Сообщение не может быть пустым. Отмена...",
        )


def load_attachs():
    attachments = []
    for i, v in enumerate(event["message"]["attachments"]):
        m = -1
        m_url = ""
        for ind, val in enumerate(event["message"]["attachments"][i]["photo"]["sizes"]):
            if val["height"] > m:
                m_url = val["url"]
        if ".jpeg" or ".jpg" in m_url:
            ext = ".jpg"
        elif ".png" in m_url:
            ext = ".png"
        else:
            ext = ""
        req = requests.get(m_url)
        server = bot.bot_vk.photos.getMessagesUploadServer()
        with open(f"photo{ext}", "wb") as f:
            f.write(req.content)
        file = open(f"photo{ext}", "rb")
        upload = requests.post(server["upload_url"], files={"photo": file},).json()
        save = bot.bot_vk.photos.saveMessagesPhoto(**upload)
        photo = f"photo{save[0]['owner_id']}_{save[0]['id']}"
        attachments.append(photo)
    atch = ",".join(attachments)
    state = db.get_session_state(event["message"]["from_id"])
    if state == "ask_for_mailing_message":
        db.update_mailing_attaches(event["message"]["from_id"], atch)
    elif state == "ask_for_call_message":
        db.update_call_attaches(event["message"]["from_id"], atch)


for event in bot.longpoll.listen():
    event = {
        "type": event.type,
        "client_info": event.object.client_info,
        "message": event.object.message,
    }
    if (
        event["type"] == EventTypes.NEW_MESSAGE.value
        and (event["message"]["text"] or event["message"]["attachments"])
        and event["message"]["out"] == 0
        and event["message"]["from_id"] == event["message"]["peer_id"]
    ):
        try:
            payload = json.loads(event["message"]["payload"])
        except KeyError:
            payload = {"button": ""}
        text = event["message"]["text"].lower()

        # :blockstart: Запуск интерфейса
        if text in ["начать", "старт", "r"]:
            if not db.is_user_exist(event["message"]["from_id"]):
                db.create_user(event["message"]["from_id"])
            if not db.is_session_exist(event["message"]["from_id"]):
                db.create_session(event["message"]["from_id"])
            bot.send_gui(pid=event["message"]["from_id"])
        # :blockend: Запуск интерфейса

        # :blockstart: Возврат на главный экран
        elif payload["button"] == "home":
            bot.send_gui(text="Главный экран", pid=event["message"]["from_id"])
        # :blockend: Возврат на главный экран

        # :blockstart: Призыв
        elif payload["button"] == "call":
            db.update_session_state(event["message"]["from_id"], "ask_for_call_message")
            if not db.call_session_exist(event["message"]["from_id"]):
                db.create_call_session(event["message"]["from_id"])
            bot.send_message(
                msg="Отправьте сообщение к призыву (есть поддержка изображений)",
                pid=event["message"]["from_id"],
                keyboard=kbs.skip(),
            )
        elif payload["button"] == "letter":
            bot.send_message(
                msg=f"Отправка клавиатуры с фамилиями на букву \"{payload['letter']}\"",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_names_keyboard(payload["letter"]),
            )
        elif payload["button"] == "student":
            ids = db.get_call_ids(event["message"]["from_id"])
            if ids:
                students = ids.split(",")
            else:
                students = [ids]
            if str(db.get_vk_id(payload["id"])) in students:
                bot.send_message(
                    msg=f"{payload['name']} уже был выбран для призыва. Пропуск.",
                    pid=event["message"]["from_id"],
                )
            else:
                db.append_to_call_ids(
                    event["message"]["from_id"], db.get_vk_id(payload["id"])
                )
                bot.send_message(
                    msg=f"{payload['name']} добавлен к списку призыва.",
                    pid=event["message"]["from_id"],
                )
        elif payload["button"] == "back":
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_call_prompt(),
            )
        elif payload["button"] == "skip":
            db.update_session_state(event["message"]["from_id"], "call_configuring")
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_call_prompt(),
            )
        elif (
            db.get_session_state(event["message"]["from_id"]) == "ask_for_call_message"
        ):
            db.update_call_message(
                event["message"]["from_id"], event["message"]["text"]
            )
            if event["message"]["attachments"]:
                load_attachs()
            bot.send_message(
                msg="Отправка клавиатуры призыва",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_call_prompt(),
            )
            db.update_session_state(event["message"]["from_id"], "call_configuring")
        elif payload["button"] == "send_to_all":
            ids = ",".join(db.get_active_students_ids())
            db.update_call_ids(event["message"]["from_id"], ids)
            bot.send_message(
                msg="Все студенты отмечены как получатели уведомления",
                pid=event["message"]["from_id"],
            )
            send_call_confirm()
        elif payload["button"] == "save":
            send_call_confirm()
        elif (
            payload["button"] == "cancel"
            and db.get_session_state(event["message"]["from_id"]) == "call_configuring"
        ):
            db.empty_call_storage(event["message"]["from_id"])
            db.update_session_state(event["message"]["from_id"], "main")
            bot.send_gui(
                text="Выполнение команды отменено.", pid=event["message"]["from_id"]
            )
        elif (
            payload["button"] == "confirm"
            and db.get_session_state(event["message"]["from_id"]) == "call_configuring"
        ):
            bot.log.info("Отправка призыва...")
            cid = db.get_conversation(event["message"]["from_id"])
            text = generate_call_message()
            attachment = db.get_call_attaches(event["message"]["from_id"])
            if attachment is None:
                attachment = ""
            bot.send_message(pid=cid, msg=text, attachment=attachment)
            db.empty_call_storage(event["message"]["from_id"])
            db.update_session_state(event["message"]["from_id"], "main")
            bot.send_gui(text="Сообщение отправлено.", pid=event["message"]["from_id"])
        elif (
            payload["button"] == "deny"
            and db.get_session_state(event["message"]["from_id"]) == "call_configuring"
        ):
            db.update_call_message(event["message"]["from_id"], " ")
            db.update_call_ids(event["message"]["from_id"], " ")
            db.update_session_state(event["message"]["from_id"], "main")
            bot.send_gui(
                text="Выполнение команды отменено.", pid=event["message"]["from_id"]
            )
        elif payload["button"] == "chconv_call":
            conv = db.get_conversation(event["message"]["from_id"])
            chat = int(str(conv)[-1])
            if chat == 1:
                db.update_conversation(event["message"]["from_id"], 2000000002)
                chat = 2
            elif chat == 2:
                db.update_conversation(event["message"]["from_id"], 2000000001)
                chat = 1
            msg = db.get_call_message(event["message"]["from_id"])
            bot.send_message(
                msg=f"Теперь это сообщение будет отправлено в "
                f"{'тестовую' if chat == 1 else 'основную'} беседу:",
                pid=event["message"]["from_id"],
            )
        elif payload["button"] == "chnames_call":
            if db.get_names_using_status(event["message"]["from_id"]):
                status = 0
            else:
                status = 1
            db.update_names_using_status(event["message"]["from_id"], status)
            send_call_confirm()
        # :blockend: Призыв

        # :blockstart: Расписание
        elif payload["button"] == "schedule":
            bot.send_message(
                msg="Отправка клавиатуры с расписанием.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_schedule_keyboard(),
            )
        elif payload["button"] == "today":
            d = Date()
            s = Schedule(d.today)
            s.get_raw()
            if s.is_exist():
                schedule = s.generate()
                bot.send_message(msg=schedule, pid=event["message"]["from_id"])
            else:
                bot.send_message(
                    msg="Расписание отсутствует.", pid=event["message"]["from_id"]
                )
        elif payload["button"] == "tomorrow":
            d = Date()
            s = Schedule(d.tomorrow)
            s.get_raw()
            if s.is_exist():
                schedule = s.generate()
                bot.send_message(msg=schedule, pid=event["message"]["from_id"])
            else:
                bot.send_message(
                    msg="Расписание отсутствует.", pid=event["message"]["from_id"]
                )
        elif payload["button"] == "day_after_tomorrow":
            d = Date()
            s = Schedule(d.day_after_tomorrow)
            s.get_raw()
            if s.is_exist():
                schedule = s.generate()
                bot.send_message(msg=schedule, pid=event["message"]["from_id"])
            else:
                bot.send_message(
                    msg="Расписание отсутствует.", pid=event["message"]["from_id"]
                )
        elif payload["button"] == "arbitrary":
            bot.send_message(
                msg="Напишите дату в формате ДД-ММ-ГГГГ.",
                pid=event["message"]["from_id"],
                keyboard=kbs.cancel(),
            )
            db.update_session_state(
                event["message"]["from_id"], "ask_for_schedule_date"
            )
        elif (
            payload["button"] == "cancel"
            and db.get_session_state(event["message"]["from_id"])
            == "ask_for_schedule_date"
        ):
            db.update_session_state(event["message"]["from_id"], "main")
            bot.send_message(
                msg="Выполнение команды отменено.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_schedule_keyboard(),
            )
        elif (
            db.get_session_state(event["message"]["from_id"]) == "ask_for_schedule_date"
        ):
            if re.match(r"^\d\d(.|-|/)\d\d(.|-|/)20\d\d$", event["message"]["text"]):
                try:
                    d = datetime.datetime.strptime(
                        event["message"]["text"], "%d-%m-%Y"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    bot.send_message(
                        msg="Неверный формат даты. Попробуйте еще раз.",
                        pid=event["message"]["from_id"],
                    )
                else:
                    s = Schedule(d)
                    s.get_raw()
                    if s.is_exist():
                        schedule = s.generate()
                        bot.send_message(
                            msg=schedule,
                            pid=event["message"]["from_id"],
                            keyboard=kbs.generate_schedule_keyboard(),
                        )
                        db.update_session_state(event["message"]["from_id"], "main")
                    else:
                        bot.send_message(
                            msg="Расписание отсутствует.\nПопробуй указать другую "
                            "дату.",
                            pid=event["message"]["from_id"],
                        )
                        db.update_session_state(
                            event["message"]["from_id"], "ask_for_schedule_date"
                        )
            else:
                bot.send_message(
                    msg="Неверный формат даты. Попробуйте еще раз.",
                    pid=event["message"]["from_id"],
                )
        # :blockend: Расписание

        # :blockstart: Рассылки
        elif payload["button"] == "mailings":
            bot.send_message(
                msg="Отправка клавиатуры со списком рассылок.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_mailings_keyboard(),
            )
        elif payload["button"] == "mailing":
            if not db.mailing_session_exist(event["message"]["from_id"]):
                db.create_mailing_session(event["message"]["from_id"])
            db.update_mailing_session(event["message"]["from_id"], payload["slug"])
            bot.send_message(
                msg=f"Меню управления рассылкой \"{payload['name']}\":",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_mailing_mgmt(
                    is_admin=bot.is_admin(event["message"]["from_id"]),
                    slug=payload["slug"],
                    user_id=event["message"]["from_id"],
                ),
            )
        elif payload["button"] == "subscribe":
            db.query(
                f"UPDATE vk_subscriptions SET {payload['slug']}=1 WHERE "
                f"user_id={payload['user_id']}"
            )
            bot.send_message(
                msg="Вы были успешно подписаны на рассылку.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_mailing_mgmt(
                    is_admin=bot.is_admin(event["message"]["from_id"]),
                    slug=payload["slug"],
                    user_id=event["message"]["from_id"],
                ),
            )
        elif payload["button"] == "unsubscribe":
            db.query(
                f"UPDATE vk_subscriptions SET {payload['slug']}=0 WHERE "
                f"user_id={payload['user_id']}"
            )
            bot.send_message(
                msg="Вы были успешно отписаны от рассылки.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_mailing_mgmt(
                    is_admin=bot.is_admin(event["message"]["from_id"]),
                    slug=payload["slug"],
                    user_id=event["message"]["from_id"],
                ),
            )
        elif payload["button"] == "send_mailing":
            db.update_session_state(
                event["message"]["from_id"], "ask_for_mailing_message"
            )
            bot.send_message(
                msg="Отправьте текст рассылки (есть поддержка изображений)",
                pid=event["message"]["from_id"],
                keyboard=kbs.cancel(),
            )
        elif (
            payload["button"] == "cancel"
            and db.get_session_state(event["message"]["from_id"])
            == "ask_for_mailing_message"
        ):
            bot.send_message(
                msg="Выполнение команды отменено. Возвращаюсь на экран управления "
                "рассылкой.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_mailing_mgmt(
                    is_admin=bot.is_admin(event["message"]["from_id"]),
                    slug=db.get_mailing_session(event["message"]["from_id"]),
                    user_id=event["message"]["from_id"],
                ),
            )
            db.update_session_state(event["message"]["from_id"], "main")
        elif (
            db.get_session_state(event["message"]["from_id"])
            == "ask_for_mailing_message"
        ):
            db.update_mailing_message(
                event["message"]["from_id"], event["message"]["text"]
            )
            if event["message"]["attachments"]:
                load_attachs()
            bot.send_message(
                msg="Всем подписчикам рассылки будет отправлено сообщение с указанным вами текстом",
                pid=event["message"]["from_id"],
                keyboard=kbs.prompt(),
                forward=f"{event['message']['id']}",
            )
            db.update_session_state(event["message"]["from_id"], "prompt_mailing")
        elif (
            payload["button"] == "confirm"
            and db.get_session_state(event["message"]["from_id"]) == "prompt_mailing"
        ):
            attach = db.get_mailing_attaches(event["message"]["from_id"])
            if attach is None:
                attach = ""
            bot.send_mailing(
                slug=db.get_mailing_session(event["message"]["from_id"]),
                text=db.get_mailing_message(event["message"]["from_id"]),
                attach=attach,
            )
            bot.send_message(
                msg="Рассылка отправлена.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_mailings_keyboard(),
            )
        elif (
            payload["button"] == "deny"
            and db.get_session_state(event["message"]["from_id"]) == "prompt_mailing"
        ):
            db.empty_mailing_storage(event["message"]["from_id"])
            bot.send_message(
                msg="Отправка рассылки отменена.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_mailings_keyboard(),
            )
        # :blockend: Рассылки

        # :blockstart: Параметры
        elif payload["button"] == "prefs":
            bot.send_message(
                msg="Параметры",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_prefs_keyboard(),
            )

        elif payload["button"] == "chconv":
            chat = db.get_conversation(event["message"]["from_id"])
            if chat == 2000000001:
                bot.send_message(
                    msg="Тестовая беседа сейчас активна",
                    pid=event["message"]["from_id"],
                    keyboard=kbs.generate_conv_selector(chat),
                )
            elif chat == 2000000002:
                bot.send_message(
                    msg="Основная беседа сейчас активна",
                    pid=event["message"]["from_id"],
                    keyboard=kbs.generate_conv_selector(chat),
                )

        elif payload["button"] == "select_main_conv":
            chat = 2000000002
            db.update_conversation(event["message"]["from_id"], chat)
            bot.send_message(
                msg="Основная беседа активна.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_conv_selector(chat),
            )
        elif payload["button"] == "select_test_conv":
            chat = 2000000001
            db.update_conversation(event["message"]["from_id"], chat)
            bot.send_message(
                msg="Тестовая беседа активна.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_conv_selector(chat),
            )

        elif payload["button"] == "names":
            status = db.get_names_using_status(event["message"]["from_id"])
            msg = (
                f"Использование имён в призыве "
                f"{'активно' if status else 'неактивно'}."
            )
            bot.send_message(
                msg=msg,
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_names_selector(status),
            )

        elif payload["button"] == "off_using_names":
            status = 0
            db.update_names_using_status(event["message"]["from_id"], status)
            bot.send_message(
                msg="Использование имён в призыве отключено.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_names_selector(bool(status)),
            )
        elif payload["button"] == "on_using_names":
            status = 1
            db.update_names_using_status(event["message"]["from_id"], status)
            bot.send_message(
                msg="Использование имён в призыве включено.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_names_selector(bool(status)),
            )
        # :blockend: Параметры

        # :blockstart: Финансы

        elif payload["button"] == "finances":
            bot.send_message(
                msg="Меню финансов",
                pid=event["message"]["from_id"],
                keyboard=kbs.finances_main(),
            )

        elif payload["button"] == "fin_category":
            db.update_active_expenses_category(
                event["message"]["from_id"], payload["slug"]
            )
            bot.send_message(
                msg=f"Меню управления статьей {payload['name']}.",
                pid=event["message"]["from_id"],
                keyboard=kbs.fin_category_menu(),
            )

        elif payload["button"] == "add_expense_cat":
            db.update_session_state(
                user_id=event["message"]["from_id"], state="ask_for_expenes_cat_title"
            )
            bot.send_message(
                msg="Отправьте название статьи расхода и сумму сбора, отделенную "
                "запятой.\n Пример: 23 февраля, 500",
                pid=event["message"]["from_id"],
                keyboard=kbs.cancel(),
            )
        elif (
            db.get_session_state(event["message"]["from_id"])
            == "ask_for_expenes_cat_title"
            and payload["button"] == "cancel"
        ):
            bot.send_message(
                msg="Операция отменена.",
                pid=event["message"]["from_id"],
                keyboard=kbs.finances_main(),
            )
        elif (
            db.get_session_state(event["message"]["from_id"])
            == "ask_for_expenes_cat_title"
        ):
            parsed = event["message"]["text"].split(",")
            name, summ = parsed
            slug = Translator().translate(name).text.lower().replace(" ", "-")
            db.add_expences_category(name, slug, summ)
            bot.send_message(
                msg=f'Новая статья "{name}" с суммой сборов {summ} р. успешно создана.',
                pid=event["message"]["from_id"],
                keyboard=kbs.finances_main(),
            )

        # :blockend: Финансы
