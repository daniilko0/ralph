import re
from datetime import datetime
from time import sleep

import pendulum
import requests
from bs4 import BeautifulSoup
from gspread import exceptions as gsprex

from bot import bot


def update_table():
    try:
        bot.gc.login()
        index = len(bot.sh_sch.col_values(1)) + 1
        bot.sh_sch.update_cell(index, 1, str_date)
        bot.sh_sch.update_cell(index, 2, hours)
        if dow == '6' or dow == '7':
            bot.sh_sch.update_cell(index + 1, 1, 'Итог:')
            bot.sh_sch.update_cell(index + 1, 2, f'=SUM(B{index - 5}:B{index})')
    except gsprex.APIError as e:
        print(f'[ERROR]: [{e.response.error.code}] – {e.response.error.message}')
        update_table()
    except (AttributeError, KeyError, ValueError):
        print('Херню ты натворил, Даня!')
    else:
        print('Архив часов обновлён.')


while True:
    dow = pendulum.now('Europe/Moscow').format('d')
    a = 1
    if dow == '6':
        a = 2
    date = pendulum.now('Europe/Moscow').add(days=a).format('YYYY-MM-DD')
    str_date = pendulum.now('Europe/Moscow').add(days=a).format('DD MMMM', locale='ru')
    del a
    req = requests.get('http://rating.ivpek.ru/timetable/timetable/show?gid=324&date={}'.format(date))
    soup = BeautifulSoup(req.text, 'lxml')
    msg_w = soup.find_all('div', {'class': 'msg warning'})
    msg_e = soup.find_all('div', {'class': 'msg error'})
    if msg_w != [] and msg_w is not None:
        print('Расписание составлено, но не опубликовано.')
        sleep(600)
    elif msg_e != [] and msg_e is not None:
        print('Расписание не опубликовано.')
        sleep(600)
    else:

        print('Расписание', end=' ')
        for span in soup.find_all('span', {'class': 'ldur'}):
            span.decompose()
        for br in soup.find_all('br'):
            soup.br.insert_before(' ')
            br.decompose()
        schedule_html = soup.find_all('table', {'class': 'tbl'})[1]
        schedule = []
        rows = schedule_html.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [el.text.strip() for el in cols]
            schedule.append([el for el in cols if el])
        schedule = [el for el in schedule if len(el) > 1]
        lessons = len(schedule)
        hours = lessons * 2
        if not schedule:
            print('отсутствует.')
            sleep(600)
        else:
            print('опубликовано.')
            msg_date = soup.find_all('span', {'class': 'yellow-msg'})[1].text
            msg = ''
            replacements = {
                'Лекция': '(Л)',
                'Лабораторная работа': '(Л/Р)',
                'Зачет': '(З)',
                'Диф. зачет': '(ДифЗ)',
                'Экзамен': '(Э)',
                '(английский язык)': ''
            }
            for i in range(len(schedule)):
                for j in range(len(schedule[i])):
                    item = schedule[i][j]
                    for k, v in replacements.items():
                        item = re.sub(k, v, item)
                    if re.findall('Иностранный язык', item):
                        lesson = re.compile(r'(?<=\()\D+(?=\))').findall(item)
                        item = 'Английский язык ({}) Кузнецова И.Н/Коротина М.А. 12/13а'.format(lesson[1])
                        schedule[i][j + 1] = ''
                    msg += '{} '.format(item)
                msg += '\n'

            if msg:
                msg = 'Расписание на {}:\n'.format(msg_date) + msg
                bot.send_mailing(ids=bot.sch_maillist, msg=msg)
                bot.send_message(pid=bot.cid, msg=msg)
                update_table()

            hour = datetime.now().hour
            pause = 0
            if 0 < hour < 5:
                pause = 5
            if 5 < hour < 10:
                pause = 24
            if 9 < hour < 15:
                pause = 19
            if 14 < hour < 19:
                pause = 15
            if 18 < hour < 23:
                pause = 11
            sleep(pause * 3600)
