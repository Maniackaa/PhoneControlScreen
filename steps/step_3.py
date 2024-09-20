import asyncio
from config.bot_settings import logger as log
from database.db import Device
from services.func import wait_new_field

logger = log.bind(step=1)


async def sms_code_input(device: Device, sms_code):

    res = await device.sendAai(
        params='{action:["click","sleep(1000)","click","sleep(500)"],query:"TP:more&&R:psw_id"}'
    )
    logger.debug(f'Клик на поле sms_code: {res.text}')
    await asyncio.sleep(1)

    # Вставка sms code
    res = await device.text(
        text=sms_code
    )
    logger.debug(f'result Вставка sms_code: {res.text}')

    # Клик на отправить
    res = await device.sendAai(
        params='{action:"click",query:"TP:more&&R:btnSubmit"}'
    )
    logger.debug(f'result Клик на отправить: {res.text}')

    await asyncio.sleep(1)
    text_on_screen = await device.text(rect=[126,427,954,2022], lang='rus', mode='multiline')
    logger.debug(text_on_screen)
    if 'неверный пароль' in text_on_screen:
        # Отклоняем платеж
        logger.info(f'Отклоняем платеж')
        return 'decline'


async def sms_code_input_kapital(device: Device, sms_code):
    await wait_new_field(device, params='{query:"R:otpPart1"}')
    await device.sendAai(params=f'{{action:"setText({sms_code[0]})",query:"R:otpPart1"}}')
    await device.sendAai(params=f'{{action:"setText({sms_code[1]})",query:"R:otpPart2"}}')
    await device.sendAai(params=f'{{action:"setText({sms_code[2]})",query:"R:otpPart3"}}')
    await device.sendAai(params=f'{{action:"setText({sms_code[3]})",query:"R:otpPart4"}}')
    while True:
        text = await device.read_screen_text(rect='[0,0,1080,2000]', lang='eng', mode='multiline')
        logger.debug(text)
        if 'wrong' in text.lower():
            logger.info(f'Отклоняем платеж')
            return 'decline'
        elif 'is on the way' in text.lower():
            logger.info(f'Подтверждаем платеж')
            return 'accept'
        await asyncio.sleep(1)
    # await wait_new_field(device, params='{query:"D:Payment is on the way"}')
    # await wait_new_field(device, params='{query:"D:Back to home page"}')