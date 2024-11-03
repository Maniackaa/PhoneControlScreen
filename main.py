import asyncio
import datetime
import json
import time

import keyboard
import structlog

from config.bot_settings import logger as log, settings
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


async def prepare(device_id):
    log.info(f'Подготовка: {device_id}')
    device = Device(device_id)
    device.device_status = DeviceStatus.END
    device.start_job_time = None
    device.device_data.set('last_screen_change', datetime.datetime.now())
    info = await device.info
    device.device_data.set('device_name', info['name'])
    device.device_data.set('height', info['height'])
    device.device_data.set('width', info['width'])
    device.device_data.set('manufacturer', info['manufacturer'])


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

def testprint2():
    print('ctrl+2')


async def key_wait():
    try:
        keyboard.add_hotkey('ctrl+1', testprint1)
        keyboard.add_hotkey('ctrl+2', testprint2)

    except Exception as err:
        print(err)
        input('Нажмите Enter')


async def test(device):
    device.logger().info('Test')
    logger2: structlog.stdlib.BoundLogger = structlog.get_logger('new')
    logger2.info('test 2')


async def main():
    asyncio.create_task(key_wait())
    await get_token()
    connected_devices_ids = set()
    while True:
        try:
            devices_ids = await device_list() or []
            if set(devices_ids) != connected_devices_ids:
                # Новые телефоны подключены
                new_device_ids = set(devices_ids) - connected_devices_ids
                if new_device_ids:
                    log.info(f'{Back.YELLOW}Подключены новые телефоны:{Style.RESET_ALL} {new_device_ids}')
                    for new_device_id in new_device_ids:
                        await prepare(new_device_id)

                disconnected_devices = connected_devices_ids - set(devices_ids)
                if disconnected_devices:
                    log.info(f'{Back.RED}ОТКЛЮЧЕНЫ телефоны:{Style.RESET_ALL} {disconnected_devices}')
                    all_task = asyncio.all_tasks(loop=None)
                    for disconnected_device_id in disconnected_devices:
                        for task in all_task:
                            task_name = task.get_name()
                            if disconnected_device_id == task_name:
                                log.warning(f'Завершаем JOB {disconnected_device_id}')
                                task.cancel()
                        pass
                connected_devices_ids = set(devices_ids)

            ready_devices = []
            device_text = ''
            for num, device_id in enumerate(devices_ids, 1):
                device = Device(device_id)
                # asyncio.create_task(test(device), name=f'{device.device_id} {str(datetime.datetime.now(tz=settings.tz))}')
                db_status = await device.db_ready_check()
                if db_status == DeviceStatus.END or db_status == DeviceStatus.READY:
                    # Если скрипт закончен или готов - проверяем экран
                    start = time.perf_counter()

                    is_ready = await device.ready_response_check()
                    # print(f'время проверки поля: {time.perf_counter() - start} c.')
                    if is_ready:
                        device.device_status = DeviceStatus.READY
                        ready_devices.append(device)
                        device_text += (
                            f'\n{num}) {device.device_data.device_name} ({device_id}): {Back.GREEN}Готов   {Style.RESET_ALL}'
                            f'({device.device_status.name} {device.device_status.value})'
                        )
                    else:
                        device_text += f'\n{num}) {device.device_data.device_name} ({device_id}): {Back.RED}Неизвестная херня!  {Style.RESET_ALL}\n'
                else:
                    timer_text = ''
                    if device.STEP2_END:
                        timer_text = f'ввод {(datetime.datetime.now() - device.STEP2_END).total_seconds()} сек. назад'
                    device_text += f'\n{num}) {device.device_data.device_name} ({device_id}): {Back.YELLOW}Занят  {Style.RESET_ALL} ({device.device_status.name} {device.device_status.value} {timer_text}timer: {device.timer}/{settings.JOB_TIME_LIMIT})\n'
            print(device_text)

            payments = await get_worker_payments()
            print(f'Платежей: {len(payments)}')
            for payment in payments:
                for device in ready_devices:
                    if device.device_status == DeviceStatus.READY:
                        if device.is_job_free:
                            device.payment = payment
                            device.device_status = DeviceStatus.STEP0
                            device.JOB_START = datetime.datetime.now()
                            result = await change_payment_status(payment_id=payment['id'], status=8)
                            if result:
                                asyncio.create_task(make_job(device), name=f'{device.device_id}')
                                log.info(f'{Back.BLUE}Стартовала задача{Style.RESET_ALL}: {device, payment}')
                                break

            await asyncio.sleep(3)
        except asyncio.TimeoutError as e:
            log.info(f'Лимит времени одно из телефонов вышел!: {e}')
        except Exception as e:
            log.error(e)
            await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as error:
        print(error)
        input('Enter')

