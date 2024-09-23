import asyncio
import datetime
import json
import time

from config.bot_settings import logger as log
from database.db import Device, DeviceStatus
from services.asu_func import get_worker_payments, get_token, check_payment, change_payment_status
from services.func import get_card_data, wait_new_field, check_field
from services.total_api import device_list

from steps.step_1 import amount_input
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input_kapital
"""5239151723408467 06/27"""


async def make_job(device):
    try:
        payment = device.payment
        payment_result = None
        logger = device.logger()
        logger.info(payment)
        payment_id = payment['id']
        card_data = json.loads(payment.get('card_data'))
        logger.debug(card_data)
        amount = str(payment['amount'])
        card = card_data['card_number']
        exp = f'{int(card_data["expired_month"]):02d}/{card_data["expired_year"]}'
        cvv = card_data['cvv']
        logger.debug(f'exp: {exp}')
        # await wait_new_field(device, params='{query:"TP:all&&D:Top up"}')

        script_start = time.perf_counter()
        device.device_status = DeviceStatus.STEP1
        logger = logger.bind(status=device.device_status)
        await amount_input(device, amount)
        device.device_status = DeviceStatus.STEP2
        logger = logger.bind(status=device.device_status)
        await card_data_input(device, card,  exp, cvv)
        device.STEP2_END = datetime.datetime.now()
        await change_payment_status(payment_id, 5)
        # Далее ждем смс. Проверяем что на экране нет ошибок
        device.device_status = DeviceStatus.STEP3
        logger = logger.bind(status=device.device_status)
        sms = ''
        while True:
            is_failed = await check_field(device, params='{query:"TP:all&&D:Transaction failed"}')
            if is_failed:
                logger.info('Найдено поле Transaction failed')
                payment_result = 'decline'
                res = await device.sendAai(params='{action:["click","sleep(500)"],query:"TP:all&&D:Back to main page"}')
                break
            is_incorrect = await check_field(device, params='{query:"TP:all&&T:Неверный срок"}') or 'Неверный номер' in await device.read_screen_text(rect='[52,238,1028,2272]', lang='rus')
            if is_incorrect:
                logger.info('Найдено поле Неверный срок или Неверный номер')
                payment_result = 'decline. restart'
                break
            payment_check = await check_payment(payment_id)
            logger.debug(payment_check)
            if payment_check.get('status') in [-1, 9]:
                # Уже отклонен. На исходную.
                payment_result = 'restart'
                logger.debug(f'Уже отклонен. На исходную.')
                break

            sms = payment_check.get('sms_code')
            if sms:
                logger.info('смс код получен')
                break
            delta = (datetime.datetime.now() - device.STEP2_END).total_seconds()
            if delta > device.SMS_CODE_TIME_LIMIT:
                payment_result = 'decline. restart'
                logger.info(f'Время получения кода вышло. payment_result: {payment_result}')
                break
            else:
                logger.debug(f'Прошло {int(delta)} с. после ввода данных карты')
            await asyncio.sleep(3)

        logger.debug(f'payment_result: {payment_result}')
        if not payment_result:
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
        # await device.restart()
        is_ready = await device.ready_check()
        if is_ready:
            device.device_status = DeviceStatus.READY
        else:
            device.device_status = DeviceStatus.UNKNOWN

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        raise err

