import json
import re
from pprint import pprint

from bot import bot

for event in bot.longpoll.listen():
    bot.event = event
    pprint(bot.event.object)
    payload = json.loads(bot.event.object.payload)
    print(payload)
    if (
        bot.event.type == bot.NEW_MESSAGE
        and bot.event.object.text
        and bot.event.object.out == 0
        and bot.event.object.from_id == bot.event.object.peer_id
    ):
        text = bot.event.object.text.lower()
        if text == "начать":
            bot.send_gui()
        elif re.match(r"\b([a-z]|sch)\b", payload["button"]):
            bot.send_message(
                msg="Отправка клавиатуры.",
                pid=bot.event.object.from_id,
                keyboard=open(
                    f'keyboards/names/{payload["button"]}.json', "r", encoding="UTF-8"
                ).read(),
            )
        elif payload["button"] == "student":
            bot.ids.append(payload["id"])
            bot.send_message(msg=f'{payload["name"]} добавлен к списку призыва.')
        elif payload["button"] == "call":
            bot.send_call()
        elif payload["button"] == "call_w_msg":
            bot.ask_for_msg()
        elif payload["button"] == "confirm":
            bot.send_message(pid=bot.cid, msg=bot.text)
            bot.text = ""
            bot.send_gui(text="Сообщение отправлено.")
        elif payload["button"] == "deny":
            bot.text = ""
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
            bot.get_debtors(col=payload["col_id"])
        elif payload["button"] == "fav":
            bot.send_message(
                msg="Отправка клавиатуры с алфавитом.",
                pid=bot.event.object.from_id,
                keyboard=open("keyboards/alphabet.json", "r", encoding="UTF-8").read(),
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
                pid=bot.event.object.from_id,
                msg="Отправьте сообщение к призыву",
                keyboard=open("keyboards/empty.json", "r", encoding="utf-8").read(),
            )
            bot.mode = "ask_for_message_partial_call"
        elif bot.mode == "ask_for_message_partial_call":
            bot.send_message(
                pid=bot.event.object.from_id,
                msg="Будет отправлено такое сообщение. Подтвердить?",
            )
            t = bot.generate_mentions(bot.ids, True) + "\n" + bot.event.object.text
            bot.show_msg(t)
        elif "отмена" in text and bot.mode == "select_letter":
            bot.send_gui("Выполнение команды отменено.")
