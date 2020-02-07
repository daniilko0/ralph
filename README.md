# RALPH
## Бот – платформа, призванный управлять студеческой беседой и упростить работу старост.
![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/dadyarri/ralph?color=brightgreen&include_prereleases)

[![Code style](https://img.shields.io/static/v1?label=Code%20style&message=black&color=black&logo=python&logoColor=white)](https://github.com/dadyarri/ralph/blob/master/LICENSE.md)
![GitHub](https://img.shields.io/github/license/dadyarri/ralph?color=brightgreen)

[![Pyup](https://pyup.io/repos/github/dadyarri/ralph/shield.svg)](https://pyup.io/account/repos/github/dadyarri/ralph/)
![Scrutinizer code quality (GitHub/Bitbucket)](https://img.shields.io/scrutinizer/quality/g/dadyarri/ralph/master)
![Travis (.org)](https://img.shields.io/travis/dadyarri/ralph)
### О проекте
RALPH - это платформа, созданная для того, чтобы упросить нелёгкий труд старост в студенческих группах.  
Он работает как бот ВКонтакте, которого можно добавить в беседу, где он и будет выполнять свои функции.
### Описание функционала
Бот управляется с помощью встроенной клавиатуры ВКонтакте. Для ее вызова в первый раз необходимо отправить сообщение с текстом "Начать" (или нажать соответствующую кнопку)
1. Призыв
    - Общий призыв (отправляет в беседу упоминание всех студентов)
    - Призыв выбранных студентов (отправляет в беседу упоминания выбранных с помощью клавиатуры студентов)
2. Призыв должников (отправка в беседу сообщения с упоминанием студентов, не сдавших деньги на указанную цель)
3. Создание рассылки по Потокам:
    - Общий канал
    - Тестовый канал
    - Расписание
    - Обновления
4. Каждым потоком можно управлять через меню "Управление рассылками"
5. Получение расписания:
    - на сегодня
    - на завтра
    - на послезавтра
    - на любую дату в формате ДД-ММ-ГГГГ

**Функции 1-3 требуют доступа администратора**

### Как занести данные о студентах в базу данных?

- Создать в корне проекта текстовый файл с именем students.txt и наполнить его следующей информацией:

        Идшник ВК:Имя:Фамилия:Номер группы:Номер подгруппы:Статус:Админ бота,
        
        где статус - число от 1 до 5:  
        1 - бюджет  
        2 - платное  
        3 - за счет учереждения  
        4 - иностранец  
        5 - отчислен  

### Вклад
Я очень благодарен каждому человеку, принесшему пользу проекту:
<table>
  <tr>
    <td align="center"><a href="https://github.com/6a16ec"><img src="https://avatars3.githubusercontent.com/u/26770482?v=" width="60"><br><sub><b>Nikita Semaev</b></sub></a></td>
  </tr>
</table>