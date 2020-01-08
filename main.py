import json
import re

import apiai

from bot import Bot
from students import students

bot = Bot()

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
        else:
            print(payload)
        text = bot.event.object.text.lower()
        if text in ["начать", "старт"]:
            bot.send_gui()
        elif re.match(r"^([a-z]|sch)$", payload["button"]):
            bot.send_message(
                msg="Отправка клавиатуры.",
                pid=bot.event.object.from_id,
                keyboard=open(
                    f'keyboards/names/{payload["button"]}.json', "r", encoding="UTF-8"
                ).read(),
            )
        elif payload["button"] == "student":
            bot.ids.append(payload["id"])
            bot.send_message(
                pid=bot.event.object.from_id,
                msg=f'{payload["name"]} добавлен к списку призыва.',
            )
        elif payload["button"] == "back":
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=bot.event.object.from_id,
                keyboard=open("keyboards/call.json", "r", encoding="UTF-8").read(),
            )
        elif payload["button"] == "call":
            bot.mode = "ask_for_msg"
            bot.send_message(
                msg="Отправьте сообщение к призыву (вложения не поддерживаются)",
                pid=bot.event.object.from_id,
                keyboard=open("keyboards/skip.json", "r", encoding="UTF-8").read(),
            )
        elif payload["button"] == "skip":
            bot.text = ""
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=bot.event.object.from_id,
                keyboard=open("keyboards/call.json", "r", encoding="UTF-8").read(),
            )
        elif payload["button"] == "send_to_all":
            bot.ids = list(students.keys())
            bot.send_message(
                msg="Все студенты отмечены как получатели уведомления. Готово к "
                'отправке, нажмите "Сохранить"',
                pid=bot.event.object.from_id,
            )
        elif payload["button"] == "confirm":
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
                    "keyboards/select_col.json", "r", encoding="UTF-8"
                ).read(),
            )
        elif payload["button"] == "col_id":
            bot.get_debtors(col=payload["id"])
        elif payload["button"] == "schedule":
            bot.send_message(
                msg="Отправка клавиатуры с расписанием.",
                pid=bot.event.object.from_id,
                keyboard=open("keyboards/schedule.json", "r", encoding="UTF-8").read(),
            )
        elif payload["button"] == "today":
            bot.get_schedule()
        elif payload["button"] == "tomorrow":
            bot.get_schedule_for_tomorrow()
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
                keyboard=open("keyboards/prompt.json", "r", encoding="UTF-8").read(),
            )
            if len(bot.ids) < 33:
                f = True
            else:
                f = False
            bot.text = f"{bot.generate_mentions(ids=bot.ids, names=f)}\n{bot.text}"
            bot.show_msg(f"{bot.text}")
        elif payload["button"] == "home":
            bot.send_gui(text="Главный экран")
        elif bot.mode == "ask_for_msg":
            bot.text = bot.event.object.text
            bot.send_message(
                msg="Отправка клавиатуры призыва",
                pid=bot.event.object.from_id,
                keyboard=open("keyboards/call.json", "r", encoding="UTF-8").read(),
            )
        elif payload["button"] == "cancel" and bot.mode == "select_letter":
            bot.text = ""
            bot.ids = []
            bot.send_gui("Выполнение команды отменено.")
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
