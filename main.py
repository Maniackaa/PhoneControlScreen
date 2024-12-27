import asyncio
import datetime
import time

import keyboard

from config.bot_settings import logger as log, settings
from database.db import Device, DeviceStatus
from job import make_job
# from services.adb_func import upload_tess_data
from services.asu_func import get_worker_payments, get_token, change_payment_status
from services.func import convert_amount_value
from services.total_api import device_list, sync_device_list
from colorama import init, Fore, Back, Style


from steps.step_1 import amount_input
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input_kapital
"""5239151723408467 06/27"""


async def restart_job(device):
    try:
        await device.restart()
    except Exception as e:
        log.error(str(e))


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

# def testprint1():
#     devices = sync_device_list()
#     print('ctrl+1')
#     print(devices)
#     for device_id in devices:
#         device = Device(device_id)
#         print(device)
#     num = input('Введите номер: ')
#     print(num)
#     # device.device_status = DeviceStatus.STEP4_3
#
# def testprint2():
#     print('ctrl+2')


# async def key_wait():
#     try:
#         keyboard.add_hotkey('ctrl+1', testprint1)
#         keyboard.add_hotkey('ctrl+2', testprint2)
#
#     except Exception as err:
#         print(err)
#         input('Нажмите Enter')


# async def test(device):
#     device.logger().info('Test')
#     logger2: structlog.stdlib.BoundLogger = structlog.get_logger('new')
#     logger2.info('test 2')


async def main():
    # asyncio.create_task(key_wait())

    await get_token()
    # upload_tess_data()
    connected_devices_ids = set()
    devices_ids = await device_list() or []
    # ["1864548471","907929276","10394501","875635955"]
    ids_list = '['
    for dev_id in devices_ids:
        id_num = '\"' + dev_id.split('@')[1] + '\",'
        ids_list += id_num

        device = Device(dev_id)
        phone_name = await device.phone_name
        log.debug(f'Проверка имени {device}: {phone_name}')
        if '_' not in phone_name:
            raise ValueError(f'{Back.YELLOW}Имя телефона "{phone_name}" не корректное{Style.RESET_ALL}')
        else:
            name, number = phone_name.split('_')
            if len(number) != 9:
                raise ValueError(f'{Back.YELLOW}Имя телефона "{phone_name}" не корректное{Style.RESET_ALL}')

    ids_list += ']'
    print(f'PHONES={ids_list}')
    input(f'список подключенных: {ids_list}')

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
            now = datetime.datetime.now()
            print(now.strftime('%H:%M:%S'))
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
                        device_balance = await device.get_raw_balance()
                        if device_balance:
                            clear_balance = convert_amount_value(device_balance)
                            device.device_data.set('balance', clear_balance)
                        device_text += (
                            f'\n{num}) {device.device_data.device_name} ({device_id}): {Back.GREEN}Готов  ({device_balance} / {device.device_data.turnover}) {Style.RESET_ALL}'
                            f'({device.device_status.name} {device.device_status.value})'
                        )
                    else:
                        device_text += f'\n{num}) {device.device_data.device_name} ({device_id}): {Back.RED}Неизвестная херня!  {Style.RESET_ALL}\n'
                        # Рестартируем
                        asyncio.create_task(restart_job(device))
                else:
                    timer_text = ''
                    if device.STEP2_END:
                        timer_text = f'ввод {(datetime.datetime.now() - device.STEP2_END).total_seconds()} сек. назад'
                    device_text += f'\n{num}) {device.device_data.device_name} ({device_id}): {Back.YELLOW}Занят  {Style.RESET_ALL} ({device.device_status.name} {device.device_status.value} {timer_text}timer: {device.timer}/{settings.JOB_TIME_LIMIT})\n'
            print(device_text)

            payments = await get_worker_payments()
            ready_devices.sort(key=lambda x: x.device_data.turnover)
            for payment in payments:
                for device in ready_devices:
                    if device.device_status == DeviceStatus.READY:
                        if device.is_job_free:

                            result = await change_payment_status(payment_id=payment['id'], status=8,
                                                                 phone_name=device.device_data.device_name,
                                                                 turnover=device.device_data.turnover,
                                                                 balance_i=device.device_data.balance)
                            if result:
                                device.payment = payment
                                device.device_status = DeviceStatus.STEP0
                                device.JOB_START = datetime.datetime.now()
                                asyncio.create_task(make_job(device), name=f'{device.device_id}')
                                log.info(f'{Back.BLUE}Стартовала задача{Style.RESET_ALL}: {device, payment}')
                                break

            await asyncio.sleep(2)
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
        input(f'{error} Enter\n')

