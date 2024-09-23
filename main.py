import asyncio
import datetime
import json
import time

from config.bot_settings import logger as log
from database.db import Device, DeviceStatus
from job import make_job
from services.asu_func import get_worker_payments, get_token, check_payment, change_payment_status
from services.func import get_card_data, wait_new_field, check_field
from services.total_api import device_list

from steps.step_1 import amount_input
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input_kapital
"""5239151723408467 06/27"""


async def main():
    await get_token()
    while True:
        try:
            devices_ids = await device_list()
            print(devices_ids)
            devices = []
            for device_id in devices_ids:
                device = Device(device_id)
                is_ready = await device.ready_check()
                if is_ready:
                    device.device_status = DeviceStatus.READY
                    devices.append(device)
                else:
                    device.device_status = DeviceStatus.UNKNOWN

            payments = await get_worker_payments()
            print(payments)
            for payment in payments:
                for device in devices:
                    if device.device_status == DeviceStatus.READY:
                        await change_payment_status(payment_id=payment['id'], status=8)
                        device.payment = payment
                        device.device_status = DeviceStatus.STEP1
                        asyncio.create_task(make_job(device))
                        print(f'Стартовала задача: {device, payment}')
                        break

            await asyncio.sleep(2)

        except Exception as err:
            log.error(err)
            await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        input('Enter')

