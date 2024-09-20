import asyncio
import json

from config.bot_settings import logger as log
from database.db import Device
from services.asu_func import get_worker_payments, get_token, check_payment, change_payment_status
from services.func import get_card_data, wait_new_field, check_field
from services.total_api import device_list

from steps.step_1 import amount_input
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input, sms_code_input_kapital
"""5239151723408467 06/27"""


async def main():
    try:
        await get_token()
        while True:
            devices = await device_list()
            print(devices)
            if devices:
                device = Device(devices[0])
                print(device)
                payments = await get_worker_payments()
                if payments:
                    payment = payments[0]
                    payment_result = None
                    logger = log.bind(device=str(device))
                    logger.info(payment)
                    payment_id = payment['id']
                    card_data = json.loads(payment.get('card_data'))
                    logger.debug(card_data)
                    amount = str(payment['amount'])
                    card = card_data['card_number']
                    exp = f'{int(card_data["expired_month"]):02d}/{card_data["expired_year"]}'
                    cvv = card_data['cvv']
                    logger.debug(f'exp: {exp}')
                    await wait_new_field(device, params='{query:"TP:all&&D:Top up"}')
                    await amount_input(device, amount)
                    await card_data_input(device, card,  exp, cvv)

                    # Далее ждем смс. Проверяем что на экране нет ошибок
                    sms = ''
                    while True:
                        is_failed = await check_field(device, params='{query:"TP:all&&D:Transaction failed"}')
                        if is_failed:
                            logger.info('Найдено поле Transaction failed')
                            payment_result = 'decline'
                            res = await device.sendAai(params='{action:["click","sleep(500)"],query:"TP:all&&D:Back to main page"}')
                            logger.debug(f'Back to home page: {res.text}')
                            break
                        is_incorrect = await check_field(device, params='{query:"TP:all&&T:Неверный срок"}') or 'Неверный номер' in await device.read_screen_text(rect='[52,238,1028,2272]', lang='rus')
                        if is_incorrect:
                            logger.info('Найдено поле Неверный срок или Неверный номер')
                            payment_result = 'decline'
                            await device.restart()
                            break
                        payment_check = await check_payment(payment_id)
                        logger.debug(payment_check)
                        sms = payment_check.get('sms_code')
                        if sms:
                            logger.info('смс код получен')
                            break
                        await asyncio.sleep(3)
                    if not payment_result:
                        payment_result = await sms_code_input_kapital(device, sms)
                    if payment_result == 'decline':
                        await change_payment_status(payment_id, -1)
                        await device.restart()
                        await asyncio.sleep(3)

                    if payment_result == 'accept':
                        await change_payment_status(payment_id, 9)
                        await device.sendAai(params='{action:["click","sleep(500)"],query:"D:Back to home page"}')

                    logger.info('Скрипт закончил')

            await asyncio.sleep(3)

    except Exception as err:
        log.error(err)
        raise err


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        raise err

