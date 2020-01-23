import datetime
import json
import re

import apiai

from bot import Bot
from keyboard import Keyboards
from schedule import Date
from schedule import Schedule
from students import students

bot = Bot()
kbs = Keyboards()

for event in bot.longpoll.listen():
    bot.event = event
    if (
        bot.event.type == bot.NEW_MESSAGE
        and bot.event.object.text
        and bot.event.object.out == 0
        and bot.event.object.from_id == bot.event.object.peer_id
    ):
        payload = {"button": ""}
        try:
            payload = json.loads(bot.event.object.payload)
        except TypeError:
            pass
        text = bot.event.object.text.lower()
        if text in ["начать", "старт"]:
            bot.send_gui()
        elif payload["button"] == "letter":
            bot.send_message(
                msg=f"Отправка клавиатуры с фамилиями на букву \"{payload['letter']}\"",
                pid=bot.event.object.from_id,
                keyboard=kbs.generate_names_keyboard(payload["letter"]),
            )
        elif payload["button"] == "student":
            pass
        elif payload["button"] == "back":
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=bot.event.object.from_id,
                keyboard=kbs.generate_alphabet_keyboard(),
            )
        elif payload["button"] == "call":
            bot.mode = "_ask_for_msg"
            bot.send_message(
                msg="Отправьте сообщение к призыву (вложения не поддерживаются)",
                pid=bot.event.object.from_id,
                keyboard=open(f"keyboards/skip.json", "r", encoding="UTF-8").read(),
            )
        elif payload["button"] == "skip":
            bot.text = ""
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=bot.event.object.from_id,
                keyboard=kbs.generate_alphabet_keyboard(),
            )
        elif payload["button"] == "send_to_all":
            bot.ids = list(students.keys())
            bot.send_message(
                msg="Все студенты отмечены как получатели уведомления. Готово к "
                'отправке, нажмите "Сохранить"',
                pid=bot.event.object.from_id,
            )
        elif payload["button"] == "confirm" and bot.mode == "_ask_for_msg":
            bot.send_message(pid=bot.cid, msg=bot.text)
            bot.text = ""
            bot.ids = []
            bot.send_gui(text="Сообщение отправлено.")
        elif payload["button"] == "deny":
            bot.text = ""
            bot.ids = []
            bot.send_gui(text="Выполнение команды отменено.")
        elif payload["button"] == "debtors":
            bot.send_message(
                msg="Выберите статью расходов (колонку в таблице)",
                pid=bot.event.object.from_id,
                keyboard=open(
                    f"keyboards/select_col.json.json", "r", encoding="UTF-8"
                ).read(),
            )
        elif payload["button"] == "col_id":
            bot.col = payload["id"]
            bot.get_debtors()
        elif payload["button"] == "schedule":
            bot.send_message(
                msg="Отправка клавиатуры с расписанием.",
                pid=bot.event.object.from_id,
                keyboard=open(
                    f"keyboards/schedule.json.json", "r", encoding="UTF-8"
                ).read(),
            )
        elif payload["button"] == "today":
            d = Date()
            s = Schedule(d.today)
            schedule = s.get()
            bot.send_message(msg=schedule, pid=bot.event.object.from_id)
        elif payload["button"] == "tomorrow":
            d = Date()
            s = Schedule(d.tomorrow)
            schedule = s.get()
            bot.send_message(msg=schedule, pid=bot.event.object.from_id)
        elif payload["button"] == "day_after_tomorrow":
            d = Date()
            s = Schedule(d.day_after_tomorrow)
            schedule = s.get()
            bot.send_message(msg=schedule, pid=bot.event.object.from_id)
        elif payload["button"] == "arbitrary":
            bot.send_message(
                msg="Напишите дату в формате ДД-ММ-ГГГГ.", pid=bot.event.object.from_id
            )
            bot.mode = "ask_for_schedule_date"
        elif payload["button"] == "chconv":
            bot.change_conversation()
        elif payload["button"] == "cancel":
            bot.ids = []
            bot.send_gui("Выполнение команды отменено.")
        elif payload["button"] == "save":
            bot.send_message(
                msg=f"В {'тестовую ' if bot.cid.endswith('1') else 'основную '}"
                f"беседу будет отправлено сообщение:",
                pid=bot.event.object.from_id,
                keyboard="keyboards/prompt.json",
            )
            if len(bot.ids) < 33:
                f = True
            else:
                f = False
            bot.text = f"{bot.generate_mentions(ids=bot.ids, names=f)}\n{bot.text}"
            bot.show_msg(f"{bot.text}")
        elif payload["button"] == "newsletter":
            bot.send_message(
                msg="Введите текст рассылки.", pid=bot.event.object.from_id
            )
            bot.mode = "wait_for_newsletter_message"
        elif payload["button"] == "home":
            bot.send_gui(text="Главный экран")
        elif bot.mode == "_ask_for_msg":
            bot.text = bot.event.object.text
            bot.send_message(
                msg="Отправка клавиатуры призыва",
                pid=bot.event.object.from_id,
                keyboard=open(
                    f"keyboards/call.json.json", "r", encoding="UTF-8"
                ).read(),
            )
        elif bot.mode == "wait_for_newsletter_message":
            bot.mode = "prompt_for_newsletter"
            bot.text = bot.event.object.text
            bot.send_message(
                msg="Всем пользователям, активировавшим бота будет отправлено "
                "следующее сообщение: ",
                pid=bot.event.object.from_id,
            )
            bot.show_msg(text=bot.text)
        elif payload["button"] == "confirm" and bot.mode == "prompt_for_newsletter":
            bot.send_mailing(msg=bot.text)
            bot.send_gui(text="Рассылка отправлена")
        elif payload["button"] == "cancel" and bot.mode == "select_letter":
            bot.text = ""
            bot.ids = []
            bot.send_gui("Выполнение команды отменено.")
        elif bot.mode == "ask_for_schedule_date":
            if re.match(r"^\d\d(.|-|/)\d\d(.|-|/)20\d\d$", bot.event.object.text):
                try:
                    d = datetime.datetime.strptime(
                        bot.event.object.text, "%d-%m-%Y"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    bot.send_message(
                        msg="Неверный формат даты. Попробуйте еще раз.",
                        pid=bot.event.object.from_id,
                    )
                else:
                    s = Schedule(d)
                    schedule = s.get()
                    bot.send_message(msg=schedule, pid=bot.event.object.from_id)
                    bot.mode = ""
            else:
                bot.send_message(
                    msg="Неверный формат даты. Попробуйте еще раз.",
                    pid=bot.event.object.from_id,
                )
        else:
            if bot.event.object.from_id != bot.gid:
                df_request = apiai.ApiAI(bot.df_key).text_request()
                df_request.lang = "ru"
                df_request.session_id = f"RALPH{bot.event.object.from_id}"
                df_request.query = bot.event.object.text
                df_response = json.loads(
                    df_request.getresponse().read().decode("utf-8")
                )
                df_response_text = df_response["result"]["fulfillment"]["speech"]
                if df_response_text:
                    bot.send_message(pid=bot.event.object.from_id, msg=df_response_text)
                else:
                    bot.send_message(
                        pid=bot.event.object.from_id, msg="Я вас не совсем понял."
                    )
