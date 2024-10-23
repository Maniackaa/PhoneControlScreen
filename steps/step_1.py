import asyncio
import datetime
import time

from config.bot_settings import logger as log
from database.db import Device, DeviceStatus
from exceptions.job_exceptions import DeviceInputAmountException
from services.asu_func import change_payment_status
from services.func import wait_new_field, check_field
from services.total_api import device_list


async def amount_input(device: Device, amount: str):
    """
        Ввод суммы
        1. Жмем кнопку Top up 'TP:more&&D:Top up'
        2. Ждем поле Top-up wallet 'TP:findText,Top-up wallet' на новом экране 60 с
        3. Клик - ввод суммы.
        4. Нажаьте продолжить 'TP:findText,Continue'. Пауза 5 c
    """

    logger = log.bind(step=device.device_status, device_id=device.device_id)
    logger.info(f'Начинается ввод суммы {amount} azn')
    is_ready = await check_field(device, '{query:"TP:more&&D:Top up"}')
    while not is_ready:
        is_ready = await check_field(device, '{query:"TP:more&&D:Top up"}')
        await asyncio.sleep(1)

    res = await device.sendAai(
        params='{action:["click","sleep(500)"],query:"TP:more&&D:Top up"}')
    device.device_status = DeviceStatus.STEP1_0
    is_ready = await check_field(device, '{query:"TP:findText,Top-up wallet"}')
    while not is_ready:
        is_ready = await check_field(device, '{query:"TP:findText,Top-up wallet"}')
        await asyncio.sleep(1)

    # Ввод суммы
    res = await device.sendAai(
        params='{action:["click","sleep(500)","setText(' + amount + ')"],query:"TP:findText,Top-up wallet&&OY:1"}')
    # await asyncio.sleep(1)
    device.device_status = DeviceStatus.STEP1_1


async def amount_input_step(device: Device, amount: str) -> bool:
    """
    Ввод суммы
    1. Жмем кнопку Top up 'TP:more&&D:Top up'
    2. Ждем поле Top-up wallet 'TP:findText,Top-up wallet' на новом экране 60 с
    3. Клик - ввод суммы.
    4. Нажаьте продолжить 'TP:findText,Continue'. Пауза 5 c
    5. Ждем экран карты 'TP:more&&R:cardPan'. Кликаем пока ждем в точку 200, 700
    """
    start = time.perf_counter()
    logger = log.bind(step=device.device_status, device_id=device.device_id)
    await amount_input(device, amount)
    # Нажатие продолжить
    res = await device.sendAai(
        params='{action:"click",query:"TP:findText,Continue"}'
    )
    device.device_status = DeviceStatus.STEP1_2
    await asyncio.sleep(7)

    text = await device.read_screen_text()
    if 'failed' in text:
        await device.restart()
        raise DeviceInputAmountException('')

    # Ждем загрузки экрана карты
    is_ready = False
    while not is_ready:
        text = await device.read_screen_text(lang='rus')
        is_ready = await check_field(device, params='{query:"TP:more&&T:Заполните данные карты"}') or 'Заполните данные карты' in text
        logger.debug(f'is_ready: {is_ready}')
        if is_ready:
            device.device_status = DeviceStatus.STEP2_0
            end = time.perf_counter()
            logger.info(f'Ввод суммы закончен. Экран ввода карты готов. ({end - start} c.)')
            break
        await asyncio.sleep(1)


async def main():
    devices = await device_list()
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        await amount_input(device, '10')
        end = time.perf_counter()
        print(end - start)


if __name__ == '__main__':
    asyncio.run(main())