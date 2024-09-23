import asyncio
import datetime
import time

from config.bot_settings import logger as log
from database.db import Device
from services.func import wait_new_field, check_field


# async def sms_code_input(device: Device, sms_code):
#
#     res = await device.sendAai(
#         params='{action:["click","sleep(1000)","click","sleep(500)"],query:"TP:more&&R:psw_id"}'
#     )
#     logger.debug(f'Клик на поле sms_code: {res.text}')
#     await asyncio.sleep(1)
#
#     # Вставка sms code
#     res = await device.text(
#         text=sms_code
#     )
#     logger.debug(f'result Вставка sms_code: {res.text}')
#
#     # Клик на отправить
#     res = await device.sendAai(
#         params='{action:"click",query:"TP:more&&R:btnSubmit"}'
#     )
#     logger.debug(f'result Клик на отправить: {res.text}')
#
#     await asyncio.sleep(1)
#     text_on_screen = await device.text(rect=[126,427,954,2022], lang='rus', mode='multiline')
#     logger.debug(text_on_screen)
#     if 'неверный пароль' in text_on_screen:
#         # Отклоняем платеж
#         logger.info(f'Отклоняем платеж')
#         return 'decline'
from services.total_api import device_list


async def sms_code_input_kapital(device: Device, sms_code) -> str:
    """
    Ввод смс кода банка Капитал
    1. Ждем поле ввода кода 'R:otpPart1'. Кликаем на 100, 940
    """
    logger = log.bind(step=3)
    text = await device.read_screen_text()
    text = text.get('value', '')
    while 'Enter dynamic password' not in text:
        await asyncio.sleep(1)
        text = await device.read_screen_text()
        text = text.get('value', '')

    field_query = '{query:"BP:editable&&IX:3"}'
    is_ready = await check_field(device, field_query)
    while not is_ready:
        await device.input(code="recentapp")
        await asyncio.sleep(1)
        await device.input(code="recentapp")
        logger.info(f'После ввода карты прошло: {(datetime.datetime.now() - device.STEP2_END).total_seconds()} с.')
        await asyncio.sleep(2)
        is_ready = await check_field(device, field_query)

    await device.sendAai(params=f'{{action:"setText({sms_code[0]})",query:"BP:editable&&IX:3"}}')
    await device.sendAai(params=f'{{action:"setText({sms_code[1]})",query:"BP:editable&&IX:4"}}')
    await device.sendAai(params=f'{{action:"setText({sms_code[2]})",query:"BP:editable&&IX:5"}}')
    await device.sendAai(params=f'{{action:"setText({sms_code[3]})",query:"BP:editable&&IX:6"}}')
    while True:
        text = await device.read_screen_text(rect='[0,0,1080,2000]', lang='eng', mode='multiline')
        logger.debug(text)
        text = text.get('value', '').lower()
        if 'wrong' in text or 'failed' in text:
            logger.info(f'Отклоняем платеж')
            return 'decline. restart'
        elif 'on the way' in text.lower():
            logger.info(f'Подтверждаем платеж')
            return 'accept'
        await asyncio.sleep(1)
    # await wait_new_field(device, params='{query:"D:Payment is on the way"}')
    # await wait_new_field(device, params='{query:"D:Back to home page"}')


async def main():
    devices = await device_list()
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        await sms_code_input_kapital(device, '0042')
        end = time.perf_counter()
        print(end - start)


if __name__ == '__main__':
    asyncio.run(main())
