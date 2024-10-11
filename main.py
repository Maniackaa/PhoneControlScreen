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
from colorama import init, Fore, Back, Style


from steps.step_1 import amount_input
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input_kapital
"""5239151723408467 06/27"""


async def prepare():
    devices_ids = await device_list()
    for num, device_id in enumerate(devices_ids, 1):
        device = Device(device_id)
        device.device_status = DeviceStatus.END


async def main():
    await get_token()
    await prepare()
    while True:
        try:
            devices_ids = await device_list()
            print(devices_ids)
            ready_devices = []
            device_text = ''
            for num, device_id in enumerate(devices_ids, 1):
                device = Device(device_id)
                db_status = await device.db_ready_check()
                if db_status == DeviceStatus.END or db_status == DeviceStatus.READY:
                    # Если скрипт закончен или готов - проверяем экран
                    is_ready = await device.ready_response_check()
                    if is_ready:
                        device.device_status = DeviceStatus.READY
                        ready_devices.append(device)
                        device_text += (
                            f'{num}) {device_id}: {Back.GREEN}Готов   {Style.RESET_ALL}'
                            f'({device.device_status}) \n'
                        )
                    else:
                        device_text += f'{num}) {device_id}: {Back.RED}Неизвестная херня!  {Style.RESET_ALL}\n'
                else:
                    device_text += f'{num}) {device_id}: {Back.YELLOW}Занят  {Style.RESET_ALL} ({device.device_status}  {device.timer})\n'
            print()
            print(device_text)

            payments = await get_worker_payments()
            print(payments)
            for payment in payments:
                for device in ready_devices:
                    if device.device_status == DeviceStatus.READY:
                        device.payment = payment
                        device.device_status = DeviceStatus.STEP1
                        device.JOB_START = datetime.datetime.now()
                        asyncio.create_task(make_job(device))
                        await change_payment_status(payment_id=payment['id'], status=8)
                        print(f'{Back.BLUE}Стартовала задача{Style.RESET_ALL}: {device, payment}')
                        break

            await asyncio.sleep(3)

        except Exception as err:
            log.error(err)
            await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        input('Enter')

