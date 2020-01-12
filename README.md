# Easybilling

Простой сервис платежной системы.

Основные пользовательские сценарии:

- Регистрация (логин/пароль)
- Авторизация
- Просмотр состояния счетов (После регистрации в ЛК создается 3 счета USD, CNY, EUR, на первый счет сразу поступает депозит 100 USD)
- Перевод средств между своими счетами (без комиссии)
- Перевод средств со своего на любой счет других клиентов (с комиссией)
- Просмотр истории переводов (доступна фильтрация и сортировка)

Запуск проекта:
`docker-compose up -d --build`
`docker-compose  exec web python init_migration.py`

Данный проект состоит из 3-й сервисов:
- NGINX
- POSTGRESQL
- BILLING (custom service GUNICORN + FLASK)

Приложение имеет 2 варианта api:
1. SSR (Service site rendering) - для UI работы с данной системой. URL начинаются с "/"
2. REST API - для подключения своего клиента. С возвратом правильных HTTPResponse-кодов. URL начинаются с "/api/"

По-умолчанию, приложение будет доступно по адресу:  http://localhost:8080/

Для начала нужно зарегистрировать пользователя. В правом верхнем углу есть кнопка 'SignUp', либо можно сразу перейти по  http://localhost:8080/signup

После этого можно заходить под созданной учеткой в саму систему.
[image]: https://ibb.co/CsMYX0k

Список url'в:

SSR:

        GET  /
        GET  /login
        POST /login     -  вход пользователя   {
                            form: email
                                  password
                            }
        GET  /signup
        POST /signup    -   создание пользователя   {
                            form: email
                                  name
                                  password
                            }
        GET  /logout
        GET  /user/<user_id>/
        POST /user/<user_id>/transaction/  - создание транзакции {
                            form: from - id счета с которого переводить
                                  to   - id счета на который переводить
                                  amount - сумма
                            }
        GET  /user/<user_id>/transaction/

API:

        POST /api/login/   -  вход пользователя   {
                                form: email
                                      password
                                }
        GET  /api/user/<user_id>/  - получение информации о пользователе и его счетах
        POST /api/user/<user_id>/transaction/ - создание транзакции {
                            form: from - id счета с которого переводить
                                  to   - id счета на который переводить
                                  amount - сумма
                            }
        GET  /api/user/<user_id>/transaction/ - получение списка транзакций пользователя


Также сделано несколько нагрузочный тестов на неоптимизированном приложении поставленному "по-умолчанию" на (Mac os, i7).
Результаты  в test/stress/README.md.
