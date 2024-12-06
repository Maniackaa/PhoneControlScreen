import asyncio
import datetime
import time

from database.db import Device, DeviceStatus
from services.asu_func import get_worker_payments, get_token
from services.func import check_field, check_bad_result

from services.total_api import device_list


async def ready_wait(device, field_query, log=None) -> bool:
    """
    Ищет поле field_query. Пока не найдет альттабит
    """
    if not log:
        log = device.logger()
    logger = log.bind(step=device.device_status)
    is_ready = await check_field(device, field_query)
    while not is_ready:
        logger.info(f'После ввода карты прошло: {(datetime.datetime.now() - device.STEP2_END).total_seconds()} с.')
        text_rus = await device.read_screen_text(lang='rus')
        if 'аутентификации' in text_rus.lower():
            logger.info('Найден выбор режима. Жму кнопульку')
            await device.click_on_field('T:Отправить')
        await asyncio.sleep(1)
        await device.alt_tab()
        is_ready = await check_field(device, field_query)
    return True


async def sms_code_input_kapital(device: Device, sms_code, log=None) -> str:
    """
    Ввод смс кода банка Капитал
    1. Ждем поле ввода кода 'R:otpPart1'. Кликаем на 100, 940
    """
    if not log:
        log = device.logger()
    logger = log.bind(step=device.device_status)
    text_eng = await device.read_screen_text()
    while 'enter dynamic' not in text_eng.lower():
        logger.debug(f'Ищем Enter dynamic')
        text_eng = await device.read_screen_text()
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
        x1 = int(12 * device.device_data.width / 100)
        x2 = int(37 * device.device_data.width / 100)
        x3 = int(62 * device.device_data.width / 100)
        x4 = int(88 * device.device_data.width / 100)
        y = int(39 * device.device_data.height / 100)
        await device.click(x1, y)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[0]}')
        await asyncio.sleep(0.5)

        await device.click(x2, y)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[1]}')
        await asyncio.sleep(0.5)

        await device.click(x3, y)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[2]}')
        await asyncio.sleep(0.5)

        await device.click(x4, y)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[3]}')
        await asyncio.sleep(1)

    device.device_status = DeviceStatus.STEP4_3

    # Ввели смс-код
    while True:
        logger.debug(f'Ввели код. Ищем концовки')
        text_eng = await device.read_screen_text()
        payment_result = await check_bad_result(device, text_eng=text_eng)
        device.device_status = DeviceStatus.STEP4_4
        if 'on the way' in text_eng.lower():
            logger.info(f'Подтверждаем платеж')
            payment_result = 'accept'
        if payment_result:
            return payment_result
        if 'enjoying the app' in text_eng.lower():
            await device.click(int(50 * device.device_data.width / 100), int(50 * device.device_data.height / 100))
        await asyncio.sleep(2)


async def sms_code_input_abb_or_rabit(device: Device, sms_code, log=None) -> str:
    # Банки: 'abb', 'rabit', 'afb', 'yelo', 'express'
    if not log:
        log = device.logger()
    logger = log.bind(step=device.device_status)
    text = await device.read_screen_text(lang='rus')
    text = text.lower()
    while 'введите' not in text:
        if device.timer > Device.SMS_CODE_TIME_LIMIT:
            return 'decline. restart'
        await asyncio.sleep(1)
        text = await device.read_screen_text(lang='rus')
        text = text.lower()
    device.device_status = DeviceStatus.STEP4_1
    payment = device.payment
    bank_name = payment['bank_name']
    log.debug(f'bank_name: {bank_name}')
    field_query = "TP:more&&R:psw_id"
    confirm_button_field = 'R:btnSubmit'

    # Ждем пока увидим поле ввода смс
    await ready_wait(device, field_query)
    device.device_status = DeviceStatus.STEP4_2

    # Вврдим код
    await device.sendAai(params=f'{{action:"setText({sms_code})",query:"{field_query}"}}')
    device.device_status = DeviceStatus.STEP4_3

    await device.click_on_field(confirm_button_field)
    device.device_status = DeviceStatus.STEP4_4
    while True:
        text_eng = await device.read_screen_text(lang='eng')
        text_eng = text_eng.lower()
        payment_result = await check_bad_result(device, text_eng=text_eng)
        if payment_result:
            return payment_result
        if 'on the way' in text_eng.lower():
            logger.info(f'Подтверждаем платеж')
            return 'accept'
        if 'enjoying the app' in text_eng.lower():
            await device.click(int(50 * device.device_data.width / 100), int(50 * device.device_data.height / 100))
        await asyncio.sleep(2)


async def sms_code_input_uni(device: Device, sms_code, log=None) -> str:
    # Банки: 'uni'
    if not log:
        log = device.logger()
    logger = log.bind(step=device.device_status)
    text = await device.read_screen_text(lang='rus')
    text = text.lower()
    while 'введите' not in text:
        if device.timer > Device.SMS_CODE_TIME_LIMIT:
            return 'decline. restart'
        await asyncio.sleep(1)
        text = await device.read_screen_text(lang='rus')
        text = text.lower()
    device.device_status = DeviceStatus.STEP4_1
    payment = device.payment
    # field_query = "TP:more&&R:Callback_sms"
    # confirm_button_field = 'TP:more&&T:Подтвердить'

    # Ждем пока увидим поле ввода смс
    # await ready_wait(device, field_query)
    device.device_status = DeviceStatus.STEP4_2

    # Вврдим код
    # await device.sendAai(params=f'{{action:"setText({sms_code})",query:"{field_query}"}}')
    device.device_status = DeviceStatus.STEP4_3

    # await device.click_on_field(confirm_button_field)
    x_coord = 40
    ratio = device.device_data.width / device.device_data.height
    logger.debug(f'ratio: {ratio}')
    if ratio == 0.45:
        y_input = 32
        y_confirm = 39
    else:
        y_input = 37.3
        y_confirm = 48.68

    # Тыкаем на поле и вставляем
    x = int(x_coord * device.device_data.width / 100)
    y = int(y_input * device.device_data.height / 100)
    await device.click(x, y)
    await asyncio.sleep(1)
    await device.text(text=f'{sms_code}')
    await asyncio.sleep(1)

    # Жмем подтвердить
    x = int(x_coord * device.device_data.width / 100)
    y = int(y_confirm * device.device_data.height / 100)
    await device.click(x, y)
    await asyncio.sleep(1)

    device.device_status = DeviceStatus.STEP4_4
    while True:
        text_eng = await device.read_screen_text(lang='eng')
        text_eng = text_eng.lower()
        payment_result = await check_bad_result(device, text_eng=text_eng)
        if payment_result:
            return payment_result
        if 'on the way' in text_eng.lower():
            logger.info(f'Подтверждаем платеж')
            return 'accept'
        if 'enjoying the app' in text_eng.lower():
            await device.click(int(50 * device.device_data.width / 100), int(50 * device.device_data.height / 100))
        await asyncio.sleep(2)



async def main():
    devices = await device_list()
    if devices:
        device = Device(devices[0])

        start = time.perf_counter()
        await get_token()
        payments = await get_worker_payments()
        print(payments)
        device = Device(device.device_id)
        device.JOB_START = datetime.datetime.now()
        device.STEP2_END = datetime.datetime.now()
        device.device_status = DeviceStatus.END
        device.start_job_time = None
        device.device_data.set('last_screen_change', datetime.datetime.now())
        info = await device.info
        print(info)
        device.device_data.set('device_name', info['name'])
        device.device_data.set('height', info['height'])
        device.device_data.set('width', info['width'])
        device.device_data.set('manufacturer', info['manufacturer'])

        device.payment = payments[0]



        await sms_code_input_uni(device, '0042')
        end = time.perf_counter()
        print(end - start)


if __name__ == '__main__':
    asyncio.run(main())
