import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
TIMEOUT = 600

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
log = logging.getLogger('TELEGRAM_BOT_APP')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

statuses = {
    'approved': (
                    'Ревьюеру всё понравилось, '
                    'можно приступать к следующему уроку.'
                ),
    'rejected': 'К сожалению в работе нашлись ошибки.'
}


def parse_homework_status(homework):
    if not all([x in homework for x in ['homework_name', 'status']]):
        log.error(
            f'Yandex Praktikum API has been changed. "homework_name",'
            f'or "status" is not in JSON: {homework}'
        )
        return 'Изменился формат API YANDEX PRAKTIKUM'

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status in statuses:
        verdict = statuses[homework_status]
        result = f'У вас проверили работу "{homework_name}"!\n\n{verdict}'

    else:
        log.error(f'Yandex Praktikum API bad status: {homework_status}')
        result = f'Неизвестный статус Yandex Praktikum API: {homework_status}'

    return result


def get_homework_statuses(raw_timestamp):
    try:
        current_timestamp = int(raw_timestamp)
        if current_timestamp < 0:
            raise ValueError

    except (ValueError, TypeError):
        log.error(f'Timestamp must be int >= 0. {raw_timestamp} given.')
        current_timestamp = int(time.time())

    params = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

    try:
        homework_statuses = requests.get(
            BASE_URL,
            headers=headers,
            params=params
        )

    except requests.exceptions.RequestException as e:
        method = e.request.method
        url = e.request.url
        headers = e.request.headers
        log.error(
            f'Error: {e} during following request:\n' +
            f'Method: {method}\n' +
            f'Headers: {headers}\n' +
            f'Url: {url}'
        )

        return {}

    return homework_statuses.json()


def send_message(message):
    try:
        response = bot.send_message(CHAT_ID, message)

    except telegram.TelegramError as e:
        cleared_message = message.replace('\n', ' ')
        log.error(
            f'Error: {e} during message to Telegram:\n' +
            f'Chat ID: {CHAT_ID}\n' +
            f'Message: {cleared_message}'
        )
        return {}

    else:
        log.info(f'Telegram Bot has sent message:\n{response}')
        return response


def main():
    log.info('Starting application')

    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            homeworks = new_homework.get('homeworks')

            if homeworks is None:
                code = new_homework.get('code')
                raise Exception(f'{code}')

            if homeworks:
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0])
                )

            else:
                log.info(f'Try again after {TIMEOUT} seconds.')

            current_timestamp = new_homework.get('current_date')
            time.sleep(TIMEOUT)

        except Exception as e:
            log.error(f'Application error: {e}')
            time.sleep(5)
            continue

    log.info('Stopping application')


if __name__ == '__main__':
    main()
