import asyncio
import datetime
import json
import time

from config.bot_settings import logger as log
from database.db import Device, DeviceStatus
from services.asu_func import get_worker_payments, get_token, check_payment, change_payment_status
from services.func import get_card_data, wait_new_field, check_field, check_bad_result
from services.total_api import device_list

from steps.step_1 import amount_input_step
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input_kapital, sms_code_input_abb

"""5239151723408467 06/27"""


async def make_job(device):
    logger = device.logger()
    logger.info(f'make_job: {device}')
    try:
        device.job_start()
        payment = device.payment
        payment_result = None
        logger = device.logger()
        logger.info(payment)
        payment_id = payment['id']
        card_data = json.loads(payment.get('card_data'))
        logger.debug(card_data)
        amount = str(payment['amount'])
        card = card_data['card_number']
        bank_name = payment['bank_name']
        exp = f'{int(card_data["expired_month"]):02d}/{card_data["expired_year"]}'
        cvv = card_data['cvv']
        logger.debug(f'exp: {exp}')
        # await wait_new_field(device, params='{query:"TP:all&&D:Top up"}')

        script_start = time.perf_counter()

        logger = logger.bind(status=device.device_status)

        await amount_input_step(device, amount)
        device.device_status = DeviceStatus.STEP2
        logger = logger.bind(status=device.device_status)

        await card_data_input(device, card,  exp, cvv)
        device.STEP2_END = datetime.datetime.now()

        await change_payment_status(payment_id, 5)
        # Далее ждем смс. Проверяем что на экране нет ошибок
        device.device_status = DeviceStatus.STEP3
        logger = logger.bind(status=device.device_status)

        sms = ''
        payment_result = ''
        while True:
            text_rus = await device.read_screen_text(lang='rus')
            text_rus = text_rus.get('value', '').lower()
            text_eng = await device.read_screen_text(lang='eng')
            text_eng = text_eng.get('value', '').lower()

            payment_check = await check_payment(payment_id)
            logger.debug(payment_check)
            if payment_check.get('status') in [-1, 9]:
                # Уже отклонен. На исходную.
                payment_result = 'restart'
                logger.debug(f'Уже отклонен. На исходную.')
                break

            payment_result = await check_bad_result(device, text_rus=text_rus, text_eng=text_eng)
            if payment_result:
                logger.info(f'Найдено плохое поле. {payment_result}')
                break

            sms = payment_check.get('sms_code')
            if sms:
                logger.info('смс код получен')
                break

            delta = (datetime.datetime.now() - device.STEP2_END).total_seconds()
            if bank_name in ['leo']:
                limit = device.LEO_WAIT_LIMIT
            else:
                limit = device.SMS_CODE_TIME_LIMIT
            if delta > limit:
                payment_result = 'decline. restart'
                logger.info(f'Время получения кода вышло. payment_result: {payment_result}')
                break

            if 'on the way' in text_eng:
                logger.info(f'Подтверждаем платеж')
                payment_result = 'accept'
                break
            else:
                logger.debug(f'Прошло {int(delta)} с. после ввода данных карты')
            await asyncio.sleep(3)

        logger.info(f'payment_result: {payment_result}')
        if not payment_result:
            if bank_name in ['abb', 'rabit']:
                payment_result = await sms_code_input_abb(device, sms)
            else:
                payment_result = await sms_code_input_kapital(device, sms)
        if 'decline' in payment_result:
            logger.info(f'Отклоняем {payment_id}')
            await change_payment_status(payment_id, -1)
            await asyncio.sleep(3)

        if payment_result == 'accept':
            logger.info(f'Подтверждаем {payment_id}')
            await change_payment_status(payment_id, 9)
            await device.sendAai(params='{action:["click","sleep(500)"],query:"D:Back to home page"}')

        if 'restart' in payment_result:
            await device.restart()

        logger.info(f'Скрипт закончил. Result: {payment_result}. Общее время: {time.perf_counter() - script_start} c.')

    except Exception as err:
        log.error(err)
        raise err

    finally:
        await device.click_on_field(field="D:Back to home page")
        device.device_status = DeviceStatus.END


if __name__ == '__main__':
    try:
        # asyncio.run(make_job())
        pass
    except Exception as err:
        log.error(err)
        raise err

