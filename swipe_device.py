import asyncio

from config.bot_settings import logger
from database.db import Device
from services.total_api import device_list


async def main():
    while True:
        devices = await device_list()
        print(devices)
        if len(devices) > 1:
            device = Device(devices[1])
            await device.input(**{"direction": "left"})
            await asyncio.sleep(2)
            await device.input(**{"direction": "right"})
            await asyncio.sleep(2)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        logger.error(err)