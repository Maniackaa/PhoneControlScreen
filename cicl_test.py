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


async def job1(device):
    print(f'Создана для {device}')
    count = 0
    total_time = 0
    while True:
        start = time.perf_counter()
        text = await device.read_screen_text(lang='eng')
        print(device.device_data.device_name, count, repr(text))
        text = await device.read_screen_text(lang='rus')
        delta = time.perf_counter() - start
        total_time += delta
        print(device.device_data.device_name, count, repr(text))
        await device.alt_tab()
        count += 1
        print(f'Средняя скорость распознавания {device.device_data.device_name:3s}: {round(total_time / count / 2, 2)}')


async def main():
    asyncio.create_task(key_wait())
    await get_token()
    devices_ids = await device_list()
    for num, device_id in enumerate(devices_ids, 1):
        device = Device(device_id)
        asyncio.create_task(job1(device))
    await asyncio.sleep(0)
    while True:
        try:
            # print('main')
            devices_ids = await device_list()
            ready_devices = []
            device_text = ''
            for num, device_id in enumerate(devices_ids, 1):
                device = Device(device_id)
                await device.info
                is_ready = await device.ready_response_check()


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

