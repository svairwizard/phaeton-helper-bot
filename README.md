<h1>#Фаэтон</h1>

Написано на 🐍 Python.

<h2>🌟Что это за проект</h2>
Проект RTR (Ready to Run). Скачал bot.py, вставил свои токены, скачал библиотеки через pip - все работает 🚀<br>
Бот, который каждое утро высылает следующую информацию<br>
- Погода на день: 🌡️Температура и ☔️вероятность осадков. Работает через API open-weather. В коде стоит город 📍Москва, но можно выбрать и другие места (через координаты)<br>
- Курс 💲доллара: Курс на утро, вчерашний курс, изменение за день. Парсим ЦБ РФ<br>
- Цена за баррель 🛢нефти Brent: Берем с сайта AlphaVantage через API. Ключ можно получить бесплатно, необходима только электронная почта<br>

<h2>🚧Планируется добавить</h2>
Дни рождения: вместе с утренней повесткой бот будет напоминать про дни рождения. Люди указываются в отдельном .json файле, как и даты их рождения. Добавление\удаление вручную

<hr>

Бот может выдавать свежую информацию по команде /now, также он ежедневно самостоятельно высылает ее в 7:00 ⏰. Время также меняется опционально при необходимости

<hr>

-⚙️Для корректной работы необходимо иметь версию ```13.7 python-telegram-bot```<br>
-✅Проверить установленную версию можно командой ```pip show python-telegram-bot```<br>
-📦Установить необходимую версию можно командой ```install python-telegram-bot==13.7```<br>

По установке библиотек - все устанавливается через ```pip```, все названия берите из import`a в начале файла. Если сами не разобрались - DeepSeek вам товарищ

