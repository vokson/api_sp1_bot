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
TIMEOUT = int(os.getenv('TIMEOUT'))

logging.basicConfig()
log = logging.getLogger('TELEGRAM_BOT_APP')
log.setLevel(logging.INFO)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    if not all([x in homework for x in ['homework_name', 'status']]):
        return 'Изменился формат API YANDEX PRAKTIKUM'

    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, ' \
            'можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

    try:
        homework_statuses = requests.get(
            BASE_URL,
            headers=headers,
            params=params
        )

    except requests.exceptions.RequestException as e:
        log.error(f'Request Error: {e}')
        return None

    else:
        return homework_statuses.json()


def send_message(message):
    try:
        response = bot.send_message(CHAT_ID, message)
    except telegram.TelegramError as e:
        log.error(f'Telegram Error: {e}')
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

            if homeworks:
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0])
                )

            elif homeworks == []:
                log.info(f'Try again after {TIMEOUT} seconds.')

            else:
                code = new_homework.get('code')
                raise Exception(f'{code}')

            current_timestamp = new_homework.get('current_date')
            time.sleep(TIMEOUT)

        except Exception as e:
            log.error(f'Application error: {e}')
            time.sleep(5)
            continue

    log.info('Stopping application')


if __name__ == '__main__':
    main()
