import asks

from contextlib import suppress
from mock import Mock, patch


class SmscApiError(Exception):

    def __init__(self, error_message):
        self.message = error_message
        super().__init__(self.message)

    def __str__(self):
        return self.message


async def mocked_asks_get(*args, **kwargs):
    response_mock = Mock()
    response_mock.text = 'Неизвестная ошибка'
    response_mock.json.return_value = {}
    if '/send' in str(args):
        response_mock.status_code = 200
        response_mock.text = ''
        response_mock.json.return_value = {'id': 175, 'cnt': 1}
    if '/status' in str(args):
        response_mock.status_code = 200
        response_mock.text = ''
        response_mock.json.return_value = {
            'status': 1,
            'last_date': '06.06.2021 22:11:21',
            'last_timestamp': 1623006681
        }
    return response_mock


@patch('asks.get', mocked_asks_get)  # Временно для целей тестирования, что бы не тратить деньги
async def request_smsc(method, login, password, payload):
    """Send request to SMSC.ru service.

    Args:
        method (str): API method. E.g. 'send' or 'status'.
        login (str): Login for account on SMSC.
        password (str): Password for account on SMSC.
        payload (dict): Additional request params, override default ones.
    Returns:
        dict: Response from SMSC API.
    Raises:
        SmscApiError: If SMSC API response status is not 200 or it has `"ERROR" in response.

    Examples:
        >>> request_smsc("send", "my_login", "my_password", {"phones": "+79123456789"})
        {"cnt": 1, "id": 24}
        >>> request_smsc("status", "my_login", "my_password", {"phone": "+79123456789", "id": "24"})
        {'status': 1, 'last_date': '28.12.2019 19:20:22', 'last_timestamp': 1577550022}
    """

    url = f'https://smsc.ru/sys/{method}.php'
    params = {
        'login': login,
        'psw': password,
        'fmt': 3,
        'charset': 'utf-8'
    }

    with suppress(asks.errors.BadStatus):
        responce = await asks.get(url, params={**params, **payload})
        responce.raise_for_status()
        reply = responce.json()
        if not reply.get('error'):
            return reply

    raise SmscApiError(responce.text)


async def send_sms(login, password, phones, text_message, queue):

    dispatch_report = await request_smsc(
        "send", login, password,
        {'phones': ','.join(phones), 'mes': text_message}
    )
    queue.put_nowait(
        {'id': dispatch_report['id'], 'phones': phones, 'message': text_message}
    )
    await queue.join()
    #  Проверяем статусы доставки sms
    #  TODO: в дальнейшем обработать статусы доставки
    for phone in phones:
        await request_smsc(
            "status", login, password,
            {'phone': phone, 'id': dispatch_report['id']}
        )
