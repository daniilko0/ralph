from bot import bot

for event in bot.longpoll.listen():
    bot.event = event
    if bot.event.type == bot.NEW_MESSAGE and bot.event.object.text and bot.event.object.out == 0 and \
            bot.event.object.from_id == bot.event.object.peer_id:
        text = bot.event.object.text.lower()

        if bot.current_is_admin():
            print('admin')

        if 'начать' in text:
            bot.send_gui()

        elif 'q' in text:
            bot.get_conversations()
        elif 'общий призыв' in text and bot.mode == 'wait_for_command':
            bot.send_call()
        elif 'призыв с сообщением' in text and bot.mode == 'wait_for_command':
            bot.ask_for_msg()
        elif 'призыв должников' in text:
            bot.send_message(pid=bot.event.object.from_id,
                             msg='Выберите статью сборов (номер колонки в таблице)',
                             keyboard=open('keyboards/select_col.json', 'r', encoding='UTF-8').read())
            bot.mode = 'select_col'
        elif 'расписание на сегодня' in text:
            bot.get_schedule()
        elif 'расписание на завтра' in text:
            bot.get_schedule_for_tomorrow()
        elif 'переключиться на основную беседу' in text:
            bot.set_active_conv_as_main()
            bot.send_gui(text='Команда успешно выполнена.')
        elif 'переключиться на тестовую беседу' in text:
            bot.set_active_conv_as_test()
            bot.send_gui(text='Команда успешно выполнена.')
        elif 'призыв выбранных' in text:
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры с алфавитом...',
                             keyboard=open('keyboards/alphabet.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_letter'
        elif bot.mode == 'ask_for_msg':
            bot.send_message(pid=bot.event.object.from_id, msg='Будет отправлено такое сообщение. Подтвердить?')
            t = bot.get_conversation_members() + '\n' + bot.event.object.text
            bot.show_msg(t)
        elif 'подтвердить' in text and bot.mode == 'confirm_msg_w_call':
            bot.send_message(pid=bot.cid, msg=bot.text)
            bot.text = ''
            bot.send_message(pid=bot.event.object.from_id, msg='Сообщение отправлено.')
            bot.send_gui(text='Команда успешно выполнена.')
        elif 'в главное меню' in text:
            bot.mode = 'wait_for_command'
            bot.send_gui(text='Выполнение команды отменено.')
        elif '4' in text and bot.mode == 'select_col':
            bot.mode = 'execute'
            bot.get_debtors(col=int(bot.event.object.text))
            bot.send_gui(text='Команда успешно выполнена.')
        elif 'сохранить' in text and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id,
                             msg='Отправьте сообщение к призыву',
                             keyboard=open('keyboards/empty.json', 'r', encoding='utf-8').read())
            bot.mode = 'ask_for_message_partial_call'
        elif bot.mode == 'ask_for_message_partial_call':
            bot.send_message(pid=bot.event.object.from_id, msg='Будет отправлено такое сообщение. Подтвердить?')
            t = bot.generate_mentions(bot.ids, True) + '\n' + bot.event.object.text
            bot.show_msg(t)
        elif 'отмена' in text and bot.mode == 'select_letter':
            bot.send_gui('Выполнение команды отменено.')
        elif text == 'а' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/a.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'б' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/b.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'г' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/g.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'д' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/d.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'е' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/e.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'ж' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/j.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'з' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/z.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'к' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/k.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'л' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/l.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'м' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/m.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'п' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/p.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'р' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/r.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'с' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/s.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif text == 'ш' and bot.mode == 'select_letter':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры со списком фамилий...',
                             keyboard=open('keyboards/names/sch.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_second_name'
        elif 'назад' in text and bot.mode == 'select_second_name':
            bot.send_message(pid=bot.event.object.from_id, msg='Отправка клавиатуры с алфавитом...',
                             keyboard=open('keyboards/alphabet.json', 'r', encoding='utf-8').read())
            bot.mode = 'select_letter'
        elif text == 'алёшин т.' and bot.mode == 'select_second_name':
            bot.ids.append('164397513')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'алиев с.' and bot.mode == 'select_second_name':
            bot.ids.append('450646082')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'астахов с.' and bot.mode == 'select_second_name':
            bot.ids.append('328169860')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'белов а.' and bot.mode == 'select_second_name':
            bot.ids.append('211502033')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'белоус д.' and bot.mode == 'select_second_name':
            bot.ids.append('214080331')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'бобылев д.' and bot.mode == 'select_second_name':
            bot.ids.append('534299949')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'гавриленко а.' and bot.mode == 'select_second_name':
            bot.ids.append('212788794')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'глазкова а.' and bot.mode == 'select_second_name':
            bot.ids.append('332479032')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'голубев д.' and bot.mode == 'select_second_name':
            bot.ids.append('549350532')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'дубакин д.' and bot.mode == 'select_second_name':
            bot.ids.append('260216591')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'ерилина а.' and bot.mode == 'select_second_name':
            bot.ids.append('217248015')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'жук а.' and bot.mode == 'select_second_name':
            bot.ids.append('138034200')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'зинин д.' and bot.mode == 'select_second_name':
            bot.ids.append('294510554')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'кириллов н.' and bot.mode == 'select_second_name':
            bot.ids.append('300517914')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'комаров а.' and bot.mode == 'select_second_name':
            bot.ids.append('190753547')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'королёв е.' and bot.mode == 'select_second_name':
            bot.ids.append('104015174')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'королёв р.' and bot.mode == 'select_second_name':
            bot.ids.append('185548061')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'королевская а.' and bot.mode == 'select_second_name':
            bot.ids.append('55674321')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'кошкина е.' and bot.mode == 'select_second_name':
            bot.ids.append('371997708')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'куликова е.' and bot.mode == 'select_second_name':
            bot.ids.append('300957594')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'курзин н.' and bot.mode == 'select_second_name':
            bot.ids.append('241050554')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'лаврентьев д.' and bot.mode == 'select_second_name':
            bot.ids.append('237163663')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'мыльников в.' and bot.mode == 'select_second_name':
            bot.ids.append('480215855')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'перелётов р.' and bot.mode == 'select_second_name':
            bot.ids.append('164885231')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'петров р.' and bot.mode == 'select_second_name':
            bot.ids.append('140861451')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'попов н.' and bot.mode == 'select_second_name':
            bot.ids.append('182343699')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'руденко д.' and bot.mode == 'select_second_name':
            bot.ids.append('416217643')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'румянцев а.' and bot.mode == 'select_second_name':
            bot.ids.append('257160362')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'сафонов п.' and bot.mode == 'select_second_name':
            bot.ids.append('552692444')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'сергеев а.' and bot.mode == 'select_second_name':
            bot.ids.append('260954580')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'солонин п.' and bot.mode == 'select_second_name':
            bot.ids.append('547085561')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'шаранин и.' and bot.mode == 'select_second_name':
            bot.ids.append('217821282')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
        elif text == 'широков и.' and bot.mode == 'select_second_name':
            bot.ids.append('202556368')
            bot.send_message(pid=bot.event.object.from_id, msg='{} добавлен в список упоминаний'
                             .format(bot.event.object.text))
