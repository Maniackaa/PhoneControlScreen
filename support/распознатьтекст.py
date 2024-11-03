import asyncio
import time

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
            res = await device.read_screen_text(lang='rus')
            print(res)

            end = time.perf_counter()
            print(end - start)
            res = await device.read_screen_text(lang='eng')
            print(res)

            print(end - start)



if __name__ == '__main__':
    asyncio.run(main())

# XIAOMI
#H 2400 W 1080

# SAMSUNG
#H 1600 W 720