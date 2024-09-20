import asyncio

from config.bot_settings import logger
from database.db import Device
from services.func import get_card_data
from services.total_api import device_list

from steps.step_1 import amount_input
from steps.step_2 import card_data_input
from steps.step_3 import sms_code_input


async def main():
    try:
        devices = await device_list()
        print(devices)
        if devices:
            device = Device(devices[0])
            print(device)
            card_data = await get_card_data()
            amount, card, exp, cvv, sms = card_data.split(';')
            await device.sendAai(params='{action:"setText(2)",query:"R:otpPart1"}')
            await device.sendAai(params='{action:"setText(3)",query:"R:otpPart2"}')
            await device.sendAai(params='{action:"setText(4)",query:"R:otpPart3"}')
            await device.sendAai(params='{action:"setText(5)",query:"R:otpPart4"}')

    except Exception as err:
        logger.error(err)



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        logger.error(err)
