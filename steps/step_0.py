import asyncio
import time

from config.bot_settings import logger
from database.db import Device
from services.func import wait_new_field


async def amount_input(device: Device, amount):
    # Ввод суммы
    res = await device.sendAai(params='{action:["click","sleep(500)","setText(' + amount + ')"],query:"TP:findText,Top-up wallet&&OY:1"}')
    print('result Ввод суммы:', res.text)
    time.sleep(1)
    # Нажатие продолжить
    res = await device.sendAai(
        params='{action:"click",query:"TP:findText,Continue"}'
    )
    print('result продолжить:', res.text)
    await asyncio.sleep(1)
    await wait_new_field(device, params='{query:"TP:more&&R:cardPan"}')
    logger.info('Ввод суммы закончен. Экран ввода карты готов')
    return True

