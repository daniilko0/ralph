"""
:project: ralph
:version: see VERSION.txt
:authors: dadyarri
:contact: https://vk.me/dadyarri
:license: MIT

:copyright: (c) 2019 - 2020 dadyarri


:release plan:
todo:
    v5.16.0:
        - Автоматически обновлять версию в статусе группы
    v5.17.0:
        - Вынести авторизацию в декоратор
    v5.18.0:
        - Вынести инструмент для создания рассылок в панель администратора
    v5.19.0:
        - Использовать payload для обработки действий с клавиатуры
    v5.20.0:
        - Добавить болталку на искуственном интеллекте
    v6.0.0:
        - Разделить бизнес-логику (собственный функционал) и обращения к API ВКонтакте и Google

"""
import binascii
import json
import os
import random
import re
from typing import NoReturn
from typing import Union

import gspread
import pendulum
import requests
import vk_api
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from vk_api.bot_longpoll import VkBotEventType

from students import students
from vkbotlongpoll import RalphVkBotLongPoll


class Bot:
    """
    Класс, описывающий объект бота, включая авторизацию в API, и все методы бота.
    """

    def __init__(self) -> None:

        print('Инициализация...')

        self.token = os.environ['VK_TOKEN']
        self.user_token = os.environ['VK_USER_TOKEN']
        self.gid = os.environ['GID_ID']
        self.cid = os.environ['CID_ID']
        self.table = os.environ['TABLE_ID']

        # Авторизация в API ВКонтакте
        print('Авторизация ВКонтакте...', end=' ')
        try:
            self.bot_session = vk_api.VkApi(token=self.token, api_version='5.103')
            self.user_session = vk_api.VkApi(token=self.user_token, api_version='5.103')
        except vk_api.exceptions.AuthError:
            print('Неудача. Ошибка авторизации.')
        else:
            try:
                self.bot_vk = self.bot_session.get_api()
                self.user_vk = self.user_session.get_api()
                self.longpoll = RalphVkBotLongPoll(vk=self.bot_session, group_id=self.gid)
            except requests.exceptions.ConnectionError:
                print('Неудача. Превышен лимит попыток подключения.')
            except vk_api.exceptions.ApiError:
                print('Неудача. Ошибка доступа.')
            else:
                print('Успех.')
                print(f'Версия API ВКонтакте: {self.bot_session.api_version}.')

        # Инициализация дополнительных переменных
        self.event = {}
        self.admins = os.environ['ADMINS_IDS'].split(',')
        self.appeal = ''

        self.mode = ''
        self.text = ''
        self.ids = []

        # Авторизация в API Google Sheets и подключение к заданной таблице
        print('Авторизация в Google Cloud...', end=' ')
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict=json.loads(
                os.environ['GOOGLE_CREDS']), scopes=self.scope)
        except binascii.Error:
            print('Неудача.')
        else:
            self.gc = gspread.authorize(credentials=credentials)
            self.table_auth = self.gc.open_by_key(key=self.table)
            self.sh = self.table_auth.get_worksheet(0)
            self.sh_sch = self.table_auth.get_worksheet(1)
            print('Успех.')

        # Переименование обрабатываемых типов событий
        self.NEW_MESSAGE = VkBotEventType.MESSAGE_NEW
        self.NEW_POST = VkBotEventType.WALL_POST_NEW

        print('Беседа...', end=' ')
        print('Тестовая' if self.cid == '2000000001' else 'Основная')

        print('Инициализация завершена.')
        self.send_message(msg='Инициализация... Успех.', pid=self.admins[0])

    def send_message(self, msg: str, pid: int = None, keyboard=None, attachments: str = None, user_ids: str = None) -> \
            NoReturn:

        """
        Отправка сообщения msg пользователю/в беседу pid
        с клавиатурой keyboard (не отправляется, если не указан json файл)
        """

        try:
            self.bot_vk.messages.send(peer_id=pid, random_id=random.getrandbits(64), message=msg, keyboard=keyboard,
                                      attachments=attachments, user_ids=user_ids)
        except vk_api.exceptions.ApiError as e:
            print(f'[ОШИБКА]: {e.__str__()}')

    def send_mailing(self, msg: str = '', attach: str = None):
        if msg == '':
            msg = 'Это просто тест.'
        pids = ','.join(self.get_conversations_ids())
        self.send_message(msg=msg,
                          attachments=attach, user_ids=pids)

    def get_conversations_ids(self):
        q = self.bot_vk.messages.getConversations(count=200, group_id=self.gid)
        _l = []
        for i in range(len(q['items'])):
            if q['items'][i]['conversation']['can_write']['allowed']:
                _l.append(q['items'][i]['conversation']['peer']['id'])
        print(_l)
        return _l

    def send_call(self) -> None:

        """
        Призывает всех студентов в активной беседе.

        Важно: Требует права администратора.
        """
        if self.current_is_admin():
            self.mode = 'execute'
            members = self.generate_mentions(list(students.keys()), names=False)
            if members is not None:
                self.send_message(pid=self.cid, msg=members)
                self.send_message(pid=self.event.object.from_id, msg=f'{self.appeal}, студенты призваны.')
                print('Студенты призваны.')
            self.mode = 'wait_for_command'

        else:
            self.send_message(pid=self.event.object.from_id, msg='{}, у тебя нет доступа к этой функции.'.format(
                self.appeal))

    def send_conversation(self) -> None:

        """
        Сообщает, какая беседа активна (тестовая или основная)

        Важно: Требует права администратора.
        """
        if self.current_is_admin():
            if self.cid == '2000000001':
                self.send_message(pid=self.event.object.from_id, msg='Тестовая беседа активна.')
            if self.cid == '2000000002':
                self.send_message(pid=self.event.object.from_id, msg='Основная беседа активна.')
        else:
            self.send_message(pid=self.event.object.from_id, msg='У тебя нет доступа к этой функции.')

    def get_schedule_for_tomorrow(self) -> None:
        """
        Получает строку с завтрашней датой (послезавтрашней, если сегодня суббота) и вызывает self.get_schedule()
        """
        dow = pendulum.now('Europe/Moscow').format('d')
        a = 1
        if dow == '6':
            a = 2
        date = pendulum.now('Europe/Moscow').add(days=a).format('YYYY-MM-DD')
        self.get_schedule(date=date)

    def get_schedule(self, date: Union[str, bool] = False) -> None:
        """
        Запрашивает расписание на указанную дату у сервера.
        """
        if not date:
            date = pendulum.now('Europe/Moscow').format('YYYY-MM-DD')
        pid = self.event.object.from_id
        req = requests.get(f'http://rating.ivpek.ru/timetable/timetable/show?gid=324&date={date}')
        soup = BeautifulSoup(req.text)
        msg_w = soup.find_all('div', {'class': 'msg warning'})
        msg_e = soup.find_all('div', {'class': 'msg error'})
        if msg_w != [] and msg_w is not None:
            self.send_message(pid=pid, msg=msg_w[0].text)
        elif msg_e != [] and msg_e is not None:
            self.send_message(pid=pid, msg=msg_e[0].text)
        else:
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

            sch_date = soup.find_all('span', {'class': 'yellow-msg'})[1].text
            msg = ''
            replacements = {
                'Лекция': '(Л)',
                'Лабораторная работа': '(Л/Р)',
                'Зачет': '(З)',
                'Диф. зачет': '(ДифЗ)',
                'Диф.зачет': '(ДифЗ)',
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

            if not msg:
                msg = 'Расписание отсутствует.'
            else:
                msg = f'Расписание на {sch_date}:\n{msg}'
            self.send_message(pid=pid, msg=msg)

    def handle_table(self, col):
        men, cash, goal = None, None, None
        try:
            self.gc.login()
            debtor_ids = []
            for i in range(5, 38):
                if self.sh.cell(i, col).value != self.sh.cell(41, col).value:
                    debtor_ids.append(self.sh.cell(i, 3).value)
        except gspread.exceptions.APIError as e:
            print(f'[ERROR]: [{e.response.error.code}] – {e.response.error.message}')
            self.handle_table(col)
        except (AttributeError, KeyError, ValueError):
            print('Херню ты натворил, Даня!')
        else:
            men = self.generate_mentions(debtor_ids, True)
            cash = self.sh.cell(41, col).value
            goal = self.sh.cell(4, col).value
        if men is not None and cash is not None and goal is not None:
            return men, cash, goal
        else:
            self.handle_table(col)

    def get_debtors(self, col):
        self.send_message(pid=self.event.object.from_id,
                          msg='{}, эта команда может работать медленно. Прошу немного подождать.'.format(
                              self.appeal))
        men, cash, goal = self.handle_table(col)
        msg = '{} вам нужно принести по {} на {}.'.format(men, cash, goal.lower())
        self.send_message(pid=self.cid, msg=msg)
        print('Должники призваны')
        self.send_message(pid=self.event.object.from_id, msg='{}, я напомнил холопам об их долгах.'
                          .format(self.appeal))
        self.send_gui(text='Команда успешно выполнена.')

    def get_conversation_members(self) -> Union[str, None]:
        """
        Возвращает строку с упоминаниями участников
        """
        conv_info = self.bot_vk.messages.getConversationMembers(peer_id=self.cid)['items']
        members_ids = []

        for i in range(len(conv_info)):
            if conv_info[i]['member_id'] > 0:
                members_ids.append(conv_info[i]['member_id'])
        return self.generate_mentions(members_ids, False)

    def get_user_info(self, identifier: Union[str, int]) -> dict:
        """
        Получить информацию о пользователе с указанным id
        """
        return self.bot_vk.users.get(user_ids=identifier, fields='sex')[0]

    def generate_mentions(self, ids: list, names: bool) -> str:
        """
        Генерирует строку с упоминаниями из списка идентификаторов
        """
        result = ''
        for i in range(len(ids)):
            if names:
                name = self.get_user_info(ids[i])['first_name']
                result += '@id{}({}), '.format(ids[i], name)
            else:
                result += '@id{}(!)'.format(ids[i])
        return result

    def change_conversation(self) -> str:
        if self.current_is_admin():
            if self.cid == '2000000001':
                self.cid = '2000000002'
                self.send_conversation()
                return self.cid
            elif self.cid == '2000000002':
                self.cid = '2000000001'
                self.send_conversation()
                return self.cid
        else:
            self.send_message(pid=self.event.object.from_id,
                              msg='У тебя нет доступа к этой функции.')

    def current_is_admin(self) -> bool:
        """
        Проверяет, является ли текущий пользователь администратором бота
        """
        return str(self.event.object.from_id) in self.admins

    def send_gui(self, text: str = 'Привет!'):
        if self.current_is_admin():
            self.send_message(pid=self.event.object.from_id,
                              msg=text,
                              keyboard=open('keyboards/admin.json', 'r', encoding="UTF-8").read())
        else:
            self.send_message(pid=self.event.object.from_id,
                              msg=text,
                              keyboard=open('keyboards/user.json', 'r', encoding="UTF-8").read())
        self.mode = 'wait_for_command'

    def ask_for_msg(self):
        self.mode = 'ask_for_msg'
        if self.current_is_admin():
            self.send_message(pid=self.event.object.from_id,
                              msg='Отправьте сообщение с текстом объявления (вложения пока не поддерживаются).',
                              keyboard=open('keyboards/empty.json', 'r', encoding="UTF-8").read())

    def show_msg(self, text: str):
        self.text = text
        self.send_message(pid=self.event.object.from_id,
                          msg=text,
                          keyboard=open('keyboards/prompt.json', 'r', encoding="UTF-8").read())
        self.mode = 'confirm_msg_w_call'


bot = Bot()
