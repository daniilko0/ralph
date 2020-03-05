import datetime
import json
import os
import re

from bot import Bot
from database import Database
from keyboard import Keyboards
from scheduler import Date
from scheduler import Schedule
from logger import init_logger

db = Database(os.environ["DATABASE_URL"])
bot = Bot()
kbs = Keyboards()
log = init_logger()

bot.update_version()


def generate_call_message():
    f = db.get_names_using_status(event["message"]["from_id"])
    students_ids = db.get_call_ids(event["message"]["from_id"])
    if students_ids:
        mentions = bot.generate_mentions(ids=students_ids, names=f)
    else:
        mentions = ""
    message = db.get_call_message(event["message"]["from_id"]) or ""
    message = f"{mentions}\n{message}"
    return message


def send_call_confirm():
    chat_id = int(str(db.get_conversation(event["message"]["from_id"]))[-1])
    message = generate_call_message()
    if message != "\n":
        bot.send_message(
            msg=f"В {'тестовую ' if chat_id == 1 else 'основную '}"
            f"беседу будет отправлено сообщение:",
            pid=event["message"]["from_id"],
            keyboard=kbs.prompt(event["message"]["from_id"]),
        )
        bot.send_message(msg=message, pid=event["message"]["from_id"])
    else:
        db.empty_call_storage(event["message"]["from_id"])
        bot.send_message(
            msg="Сообщение не может быть пустым. Отмена...",
            pid=event["message"]["from_id"],
            keyboard=kbs.generate_main_menu(bot.is_admin(event["message"]["from_id"])),
        )


for event in bot.longpoll.listen():
    event = {
        "type": event.type,
        "client_info": event.object.client_info,
        "message": event.object.message,
    }
    if (
        event["type"] == bot.NEW_MESSAGE
        and event["message"]["text"]
        and event["message"]["out"] == 0
        and event["message"]["from_id"] == event["message"]["peer_id"]
    ):

        if not db.is_user_exist(event["message"]["from_id"]):
            db.create_user(event["message"]["from_id"])
        if not db.is_session_exist(event["message"]["from_id"]):
            db.create_session(event["message"]["from_id"])
        try:
            payload = json.loads(event["message"]["payload"])
        except KeyError:
            payload = {"button": ""}
        text = event["message"]["text"].lower()

        # :blockstart: Перезапуск интерфейса
        if text in ["начать", "старт"]:
            bot.send_gui(pid=event["message"]["from_id"])
        # :blockend: Перезапуск интерфейса

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
                msg="Отправьте сообщение к призыву (вложения не поддерживаются)",
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
                keyboard=kbs.generate_alphabet_keyboard(),
            )
        elif payload["button"] == "skip":
            db.update_session_state(event["message"]["from_id"], "call_configuring")
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_alphabet_keyboard(),
            )
        elif (
            db.get_session_state(event["message"]["from_id"]) == "ask_for_call_message"
        ):
            db.update_call_message(
                event["message"]["from_id"], event["message"]["text"]
            )
            bot.send_message(
                msg="Отправка клавиатуры призыва",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_alphabet_keyboard(),
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
            log.info("Отправка призыва...")
            cid = db.get_conversation(event["message"]["from_id"])
            text = generate_call_message()
            bot.send_message(pid=cid, msg=text)
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
            schedule = s.parse()
            if schedule:
                bot.send_message(msg=schedule, pid=event["message"]["from_id"])
            else:
                bot.send_message(
                    msg="Расписание отсутствует.", pid=event["message"]["from_id"]
                )
        elif payload["button"] == "tomorrow":
            d = Date()
            s = Schedule(d.tomorrow)
            schedule = s.parse()
            if schedule:
                bot.send_message(msg=schedule, pid=event["message"]["from_id"])
            else:
                bot.send_message(
                    msg="Расписание отсутствует.", pid=event["message"]["from_id"]
                )
        elif payload["button"] == "day_after_tomorrow":
            d = Date()
            s = Schedule(d.day_after_tomorrow)
            schedule = s.parse()
            if schedule:
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
                    schedule = s.parse()
                    if schedule:
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
                msg="Отправьте текст рассылки (вложения не поддерживаются)",
                pid=event["message"]["from_id"],
                keyboard=kbs.cancel(),
            )
        elif (
            payload["button"] == "cancel"
            and db.get_session_state(event["message"]["from_id"])
            == "ask_for_mailing_message"
        ):
            bot.send_message(
                msg="Выполнение команды отменено",
                pid=event["message"]["from_id"],
                keyboard=kbs.generate_main_menu(
                    bot.is_admin(event["message"]["from_id"])
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
            subscs = db.fetch_subcribers(
                db.get_mailing_session(event["message"]["from_id"])
            )
            bot.send_message(
                msg=db.get_mailing_message(event["message"]["from_id"]),
                user_ids=subscs,
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
