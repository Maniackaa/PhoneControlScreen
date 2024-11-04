import asyncio
import json
import time

from config.bot_settings import logger
from database.db import Device
from services.total_api import device_list


async def main():
    devices = await device_list()
    print(devices)
    # while True:
    for device in devices:
        if device:
            device = Device(device)
            print(await device.info)
            start = time.perf_counter()
            # res = await device.read_screen_text(lang='rus')
            # print(res)
            # device.logger().info(f'{res}')
            #

            # print(end - start)
            res = await device.read_screen_text(rect='[0,20,100,80]', lang='eng')
            # print(res)
            # try:
            #     logger.info(f'{json.dumps(res, ensure_ascii=False)}')
            # except Exception as e:
            #     raise e
            end = time.perf_counter()
            print(end - start)



if __name__ == '__main__':
    asyncio.run(main())

# XIAOMI
#H 2400 W 1080

# SAMSUNG
#H 1600 W 720