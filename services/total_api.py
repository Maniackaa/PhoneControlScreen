import asyncio
import base64
import dataclasses
import json

import requests

from config.bot_settings import settings, logger
from database.db import TOKEN, Device

basic_url = 'http://localhost:8090/TotalControl/v2/devices?token=' + TOKEN


async def device_list():
    result = requests.get(f"{basic_url}" + '&q=all')
    result = result.json().get('ids')
    if result == 'null':
        return []
    return result



async def main():
    try:
        print(await device_list())

    except Exception as err:
        logger.error(err)
        input('Нажмите Enter')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        logger.error(err)
        input('Нажмите Enter')
device = Device('1245')

