# Рассылка SMS и её отслеживание (прототип)

Веб-приложение для рассылки SMS по базе номеров и отслеживания их доставки.

<img src="https://dvmn.org/filer/canonical/1581177685/497/">


## Как установить

- Скачайте код

- Установите виртуальное окружение. Понадобится python версии 3.8 или старше.

- Установите пакеты:

```python3
  pip install -r requirements.txt
```


## Переменные окружения

`SMSC_LOGIN` - Логин сервиса рассылки sms [https://smsc.ru](https://smsc.ru).

`SMSC_PSW` - Пароль для доступа к сервису рассылки sms [https://smsc.ru](https://smsc.ru).

`REDIS_HOST` - Адрес хоста на котором поднята база данных redis.

`REDIS_PORT` - Порт доступа к базе данных redis.

`REDIS_PASSWORD` - Пароль для доступа к базе данных redis.

`PHONE_NUMBERS` - Список телефонных номеров через запятую в формате +79********0.

`HOST` - Адрес на котором будет запущен web сервер. Необязательный параметр, по умолчанию `127.0.0.1:5000`.


## Как запустить

- Запустите web сервер следующей командой в терминале:

```python3
  python quart_server.py
```

- Откройте в браузере адрес на котором запущен web сервер, по умолчанию `127.0.0.1:5000`.


## Как использовать

В поле "Новая рассылка" ввести текст sms сообщения и нажать кнопку "Отправить". Через некоторое время новая рассылка появится ниже в истории рассылок.


## Как протестировать

Протестировать подключение к базе данных redis можно с помощью следующей команды:

```python3

python trio_db_example.py --address="redis://REDIS_HOST:REDIS_PORT" --password="REDIS_PASSWORD"

```


## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
