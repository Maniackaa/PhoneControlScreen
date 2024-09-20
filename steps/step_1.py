import asyncio
import time

from config.bot_settings import logger as log
from database.db import Device
from services.func import wait_new_field


logger = log.bind(step=1)


async def amount_input(device: Device, amount):
    res = await device.sendAai(
        params='{action:["click","sleep(500)"],query:"TP:more&&D:Top up"}')
    logger.debug(f'result клик: {res.text}')
    await wait_new_field(device, params='{query:"TP:findText,Top-up wallet"}')
    # Ввод суммы
    res = await device.sendAai(params='{action:["click","sleep(500)","setText(' + amount + ')"],query:"TP:findText,Top-up wallet&&OY:1"}')
    logger.debug(f'result Ввод суммы: {res.text}')
    await asyncio.sleep(1)
    # Нажатие продолжить
    res = await device.sendAai(
        params='{action:"click",query:"TP:findText,Continue"}'
    )
    logger.debug('result продолжить: {res.text}')
    await asyncio.sleep(1)
    await wait_new_field(device, params='{query:"TP:more&&R:cardPan"}')
    logger.info('Ввод суммы закончен. Экран ввода карты готов')
    return True

