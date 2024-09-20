import asyncio

from config.bot_settings import logger as log
from database.db import Device
from services.func import wait_new_field

logger = log.bind(step=1)


async def card_data_input(device: Device, card, exp, cvv):
    res = await device.sendAai(
        params='{action:["click","sleep(1000)","click","sleep(500)"],query:"TP:more&&R:cardPan"}'
    )
    logger.debug(f'Клик на поле карты: {res.text}')
    await asyncio.sleep(1)

    # Вставка номера карты
    res = await device.text(
        text=card
    )
    logger.debug(f'result Вставка номера карты: {res.text}')
    await asyncio.sleep(0.5)

    # Клик на exp
    res = await device.sendAai(
        params='{action:"click",query:"TP:more&&R:expDate"}'
    )
    logger.debug(f'result Клик на exp: {res.text}')
    await asyncio.sleep(0.5)
    # Вставка exp
    res = await device.text(text=exp)
    logger.debug(f'result Вставка exp: {res.text}'
          )
    await asyncio.sleep(0.5)

    # Клик на cvv
    res = await device.sendAai(
        params='{action:"click",query:"TP:more&&R:cvv"}'
    )
    logger.debug(f'result Клик на cvv: {res.text}')
    await asyncio.sleep(0.5)
    # Вставка cvv
    res = await device.text(text=cvv)
    logger.debug(f'result Вставка cvv: {res.text}')
    await asyncio.sleep(0.5)

    # Клик на продолжить
    res = await device.sendAai(
        params='{action:"click",query:"TP:more&&R:card-pay-btn"}'
    )
    logger.debug(f'result Клик на cvv: {res.text}')
    await asyncio.sleep(3)

    # Ждем экран кода
    # res = await wait_new_field(device, params='{query:"TP:more&&R:psw_id"}')
    # if res:
    #     logger.info('Ввод данных карты завершен. Экран кода загружен')
    #     return True
