import asyncio
import datetime
import json
import time

from colorama import Back, Style

from config.bot_settings import logger as log
from database.db import Device, DeviceStatus
from exceptions.job_exceptions import DeviceInputAmountException
from services.asu_func import get_worker_payments, get_token, check_payment, change_payment_status
from services.func import get_card_data, wait_new_field, check_field, check_bad_result
from services.total_api import device_list

from steps.step_1 import amount_input_step
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input_kapital, sms_code_input_abb

"""5239151723408467 06/27"""


async def make_job(device):
    logger = device.logger()
    logger.debug(f'make_job: {device}')
    logger = logger.bind(device_id=device.device_id)
    try:
        device.job_start()
        payment = device.payment
        logger.debug(payment)
        payment_id = payment['id']
        card_data = json.loads(payment.get('card_data'))
        logger.debug(card_data)
        amount = str(payment['amount'])
        card = card_data['card_number']
        bank_name = payment['bank_name']
        exp = f'{int(card_data["expired_month"]):02d}/{card_data["expired_year"]}'
        cvv = card_data['cvv']

        script_start = time.perf_counter()
        await amount_input_step(device, amount)
        await card_data_input(device, card,  exp, cvv)
        device.STEP2_END = datetime.datetime.now()  # Время ввода данных карты

        await change_payment_status(payment_id, 5)
        device.device_status = DeviceStatus.STEP3_0
        # Далее ждем смс. Проверяем что на экране нет ошибок
        sms = ''
        payment_result = ''
        if bank_name in ['leo']:
            sms_limit_time = device.LEO_WAIT_LIMIT
        else:
            sms_limit_time = device.SMS_CODE_TIME_LIMIT
        while not payment_result:
            payment_check = await check_payment(payment_id)
            logger.debug(payment_check)
            if payment_check.get('status') in [-1, 9]:
                # Уже отклонен. На исходную.
                payment_result = 'restart'
                logger.debug(f'Уже отклонен. На исходную.')
                break

            text_rus = await device.read_screen_text(lang='rus')
            text_eng = await device.read_screen_text(lang='eng')
            payment_result = await check_bad_result(device, text_rus=text_rus, text_eng=text_eng)
            if payment_result:
                logger.info(f'Найдено плохое поле. {payment_result}')
                break

            sms = payment_check.get('sms_code')
            if sms:
                device.device_status = DeviceStatus.STEP3_1
                logger.info('смс код получен')
                break

            # Сколько прошло со ввода карты
            delta = (datetime.datetime.now() - device.STEP2_END).total_seconds()
            if delta > sms_limit_time:
                payment_result = 'decline. restart'
                logger.info(f'{Back.YELLOW}Время получения кода вышло.{Style.RESET_ALL} payment_result: {payment_result}')
                break

            if 'on the way' in text_eng:
                logger.info(f'Подтверждаем платеж')
                payment_result = 'accept'
                break

            logger.info(f'Прошло {int(delta)} с. после ввода данных карты')
            await asyncio.sleep(3)

        logger.info(f'payment_result: {payment_result}')
        device.device_status = DeviceStatus.STEP4_0
        if not payment_result:
            if bank_name in ['abb', 'rabit']:
                payment_result = await sms_code_input_abb(device, sms)
            else:
                payment_result = await sms_code_input_kapital(device, sms)
        device.device_status = DeviceStatus.STEP4_5

        if 'decline' in payment_result:
            logger.info(f'Отклоняем {payment_id}')
            await change_payment_status(payment_id, -1)

        if payment_result == 'accept':
            logger.info(f'Подтверждаем {payment_id}')
            await change_payment_status(payment_id, 9)
            await device.sendAai(params='{action:["click","sleep(500)"],query:"D:Back to home page"}')
            await asyncio.sleep(5)

        if 'restart' in payment_result:
            await device.restart()

        logger.info(f'Логика закончена. {Back.GREEN}Result: {payment_result}.{Style.RESET_ALL} Общее время: {time.perf_counter() - script_start} c.')

    except asyncio.TimeoutError as e:
        log.warning(f'Timeout: {e}')
        await change_payment_status(device.payment['id'], -1)
        logger.info('Платеж отклонен')

    except DeviceInputAmountException as e:
        logger.info('Отправляем платеж заново боту. Телефон на рестарт')
        await change_payment_status(device.payment['id'], 4)

    except Exception as e:
        log.error(f'Непредвиттденная ошибка: {e}')
        raise e

    finally:
        await device.click_on_field(field="D:Back to home page")
        device.start_job_time = None
        is_ready = await check_field(device, '{query:"TP:more&&D:Top up"}')
        if is_ready:
            pass
        else:
            # text_rus = await device.read_screen_text(lang='rus')
            # text_rus = text_rus.get('value', '').lower()
            # text_eng = await device.read_screen_text(lang='eng')
            # text_eng = text_eng.get('value', '').lower()
            # bad = await check_bad_result(device, text_rus, text_eng)
            await device.restart()
        device.device_status = DeviceStatus.END
        logger.info('Телефон готов после скрипта')


if __name__ == '__main__':
    try:
        # asyncio.run(make_job())
        pass
    except Exception as err:
        log.error(err)
        raise err

