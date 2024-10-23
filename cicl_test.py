import asyncio
import datetime
import json
import time

import keyboard

from config.bot_settings import logger as log
from database.db import Device, DeviceStatus
from job import make_job
from services.asu_func import get_worker_payments, get_token, check_payment, change_payment_status
from services.func import get_card_data, wait_new_field, check_field
from services.total_api import device_list, sync_device_list
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


def testprint1():
    devices = sync_device_list()
    print('ctrl+1')
    print(devices)
    for device_id in devices:
        device = Device(device_id)
        print(device)
    num = input('Введите номер: ')
    print(num)
    # device.device_status = DeviceStatus.STEP4_3


async def key_wait():
    try:
        keyboard.add_hotkey('ctrl+1', testprint1)
    except Exception as err:
        print(err)
        input('Нажмите Enter')


async def job1():
    while True:
        print(f'job1')
        await asyncio.sleep(1)


async def main():
    asyncio.create_task(key_wait())
    await get_token()
    await prepare()
    tasks = [asyncio.create_task(job1())]
    while True:
        try:
            print('main')
            devices_ids = await device_list()
            ready_devices = []
            device_text = ''
            for num, device_id in enumerate(devices_ids, 1):
                device = Device(device_id)
                print(await device.info)

            await asyncio.sleep(3)
            done, pending = await asyncio.wait(tasks, timeout=10)
            print(done)
            print(pending)

        except asyncio.TimeoutError:
            print('Время1')

        except TimeoutError:
            print('Время2')
        except Exception as err:
            log.error(err)
            await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        input('Enter')

