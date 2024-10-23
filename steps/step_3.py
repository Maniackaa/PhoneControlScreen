import asyncio
import datetime
import time

from config.bot_settings import logger as log
from database.db import Device, DeviceStatus
from services.func import check_field, check_bad_result

from services.total_api import device_list


async def ready_wait(device, field_query) -> bool:
    """
    Ищет поле field_query. Пока не найдет альттабит
    :param device:
    :param field_query:
    :return:
    """
    is_ready = await check_field(device, field_query)
    while not is_ready:
        await device.alt_tab()
        log.info(f'После ввода карты прошло: {(datetime.datetime.now() - device.STEP2_END).total_seconds()} с.')
        await asyncio.sleep(2)
        is_ready = await check_field(device, field_query)
        await asyncio.sleep(1)
    return True


async def sms_code_input_kapital(device: Device, sms_code) -> str:
    """
    Ввод смс кода банка Капитал
    1. Ждем поле ввода кода 'R:otpPart1'. Кликаем на 100, 940
    """
    logger = log.bind(step=device.device_status, device_id=device.device_id)
    text_eng = await device.read_screen_text()
    while 'enter dynamic' not in text_eng.lower():
        logger.debug(f'Ищем Enter dynamic')
        await asyncio.sleep(1)
        payment_result = await check_bad_result(device)
        if payment_result:
            device.device_status = DeviceStatus.STEP4_5
            return payment_result

    # Текст Enter dynamic есть ан экране

    device.device_status = DeviceStatus.STEP4_1
    # field_query = '{query:"TP:more&&R:otpPart1"}'
    # await ready_wait(device, field_query)
    device.device_status = DeviceStatus.STEP4_2

    # await device.sendAai(params=f'{{action:"setText({sms_code[0]})",query:"BP:editable&&IX:3"}}')
    # await device.sendAai(params=f'{{action:"setText({sms_code[1]})",query:"BP:editable&&IX:4"}}')
    # await device.sendAai(params=f'{{action:"setText({sms_code[2]})",query:"BP:editable&&IX:5"}}')
    # await device.sendAai(params=f'{{action:"setText({sms_code[3]})",query:"BP:editable&&IX:6"}}')

    if not await device.check_field('TP:more&&R:otpPart1'):
        await device.alt_tab()

    if await device.check_field('TP:more&&R:otpPart1'):
        logger.debug('Найдены поля для цифр')
        await device.sendAai(params=f'{{action:"setText({sms_code[0]})",query:"TP:more&&R:otpPart1"}}')
        await asyncio.sleep(0.5)
        await device.sendAai(params=f'{{action:"setText({sms_code[1]})",query:"TP:more&&R:otpPart2"}}')
        await asyncio.sleep(0.5)
        await device.sendAai(params=f'{{action:"setText({sms_code[2]})",query:"TP:more&&R:otpPart3"}}')
        await asyncio.sleep(0.5)
        await device.sendAai(params=f'{{action:"setText({sms_code[3]})",query:"TP:more&&R:otpPart4"}}')
        await asyncio.sleep(0.5)
    else:
        logger.debug('Не найдены поля для цифр')
        await device.click(150, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[0]}')
        await asyncio.sleep(0.5)

        await device.click(400, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[1]}')
        await asyncio.sleep(0.5)

        await device.click(680, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[2]}')
        await asyncio.sleep(0.5)

        await device.click(950, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[3]}')
        await asyncio.sleep(1)

    device.device_status = DeviceStatus.STEP4_3

    # Ввели смс-код
    while True:
        payment_result = await check_bad_result(device)
        device.device_status = DeviceStatus.STEP4_4
        if 'on the way' in text_eng.lower():
            logger.info(f'Подтверждаем платеж')
            payment_result = 'accept'
        if payment_result:
            return payment_result
        await asyncio.sleep(2)


async def sms_code_input_abb(device: Device, sms_code) -> str:
    logger = log.bind(step=device.device_status, device_id=device.device_id)
    text = await device.read_screen_text(lang='rus')
    text = text.lower()
    while 'введите' not in text:
        if device.timer > Device.SMS_CODE_TIME_LIMIT:
            return 'decline. restart'
        await asyncio.sleep(1)
        text = await device.read_screen_text(lang='rus')
        text = text.lower()
    device.device_status = DeviceStatus.STEP4_1
    field_query = '{query:"TP:more&&R:psw_id"}'
    # Ждем пока увидим поле ввода смс
    await ready_wait(device, field_query)
    device.device_status = DeviceStatus.STEP4_2

    # Вврдим код
    await device.sendAai(params=f'{{action:"setText({sms_code})",query:"TP:more&&R:psw_id"}}')
    device.device_status = DeviceStatus.STEP4_3
    await device.click_on_field('R:btnSubmit')
    device.device_status = DeviceStatus.STEP4_4
    while True:
        text_eng = await device.read_screen_text(lang='eng')
        text_eng = text_eng.lower()
        text_rus = await device.read_screen_text(lang='rus')
        text_rus = text_rus.lower()
        payment_result = await check_bad_result(device, text_rus, text_eng)
        if payment_result:
            return payment_result
        if 'on the way' in text_eng.lower():
            logger.info(f'Подтверждаем платеж')
            return 'accept'
        await asyncio.sleep(2)


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
