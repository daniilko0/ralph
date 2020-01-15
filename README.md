# RALPH
## Бот – платформа, призванный управлять студеческой беседой и упростить работу старост.
![Code style](https://img.shields.io/static/v1?label=Code%20style&message=black&color=black&logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/static/v1?label=License&message=MIT&color=brightgreen)](https://opensource.org/licenses/MIT)

[![Pyup](https://pyup.io/repos/github/dadyarri/ralph/shield.svg)](https://pyup.io/account/repos/github/dadyarri/ralph/)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/dadyarri/ralph/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/dadyarri/ralph/?branch=master)
[![Build Status](https://travis-ci.org/dadyarri/ralph.svg?branch=master)](https://travis-ci.org/dadyarri/ralph)
### О проекте
RALPH - это платформа, созданная для того, чтобы упросить нелёгкий труд старост в студенческих группах.  
Он работает как бот ВКонтакте, которого можно добавить в беседу, где он и будет выполнять свои функции.
### Описание функционала
Бот управляется с помощью встроенной клавиатуры ВКонтакте. Для ее вызова в первый раз необходимо отправить сообщение с текстом "Начать" (или нажать соответствующую кнопку)
1. Общий призыв (отправка в беседу сообщения с упоминаниями всех студентов)
2. Призыв с сообщением (отправка в беседу сообщения с упоминанием всех студентов, плюс указанное объявление)
3. Призыв должников (отправка в беседу сообщения с упоминанием студентов, не сдавших деньги на указанную цель)
4. Создание рассылки для всех пользователей, активироваших бота (временное поведение)
5. Получение расписания на сегодня
6. Получение расписания на завтра

**Функции 1-4 требуют доступа администратора**

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
<div style="display:flex; flex-direction: row; align-items: space-between; border: 1px solid black">
<img src="https://avatars3.githubusercontent.com/u/26770482?v=" width="60">
<p><a href="https://github.com/6a16ec">6a16ec</a></p>
</div>