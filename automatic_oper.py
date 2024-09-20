import asyncio
import json

from config.bot_settings import logger as log
from database.db import Device
from services.asu_func import get_worker_payments, get_token, check_payment, change_payment_status
from services.func import get_card_data, wait_new_field
from services.total_api import device_list

from steps.step_1 import amount_input
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input, sms_code_input_kapital
"""5239151723408467 06/27 499"""


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
                    logger = log.bind(device=device)
                    logger.info(payment)
                    payment_id = payment['id']
                    card_data = json.loads(payment.get('card_data'))
                    logger.debug(card_data)
                    amount = card_data['amount']
                    card = card_data['card_number']
                    exp = f'{card_data["expired_month"]}/{card_data["expired_year"]}'
                    cvv = card_data['cvv']
                    await wait_new_field(device, params='{query:"TP:all&&D:Top up"}')
                    await amount_input(device, amount)
                    await card_data_input(device, card,  exp, cvv)
                    while True:
                        payment_check = await check_payment(payment_id)
                        logger.debug(payment_check)
                        sms = payment_check.get('sms_code')
                        if sms:
                            logger.info('смс код получен')
                            break
                        await asyncio.sleep(3)
                    res = await sms_code_input_kapital(device, sms)
                    if res == 'decline':
                        await change_payment_status(payment_id, -1)

                    if res == 'accept':
                        await change_payment_status(payment_id, 9)
                        await device.sendAai(params='{action:["click","sleep(500)"],query:"D:Back to home page"}')

                    logger.info('Скрипт закончил')

                else:
                    await asyncio.sleep(3)

    except Exception as err:
        log.error(err)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        input('Enter')
