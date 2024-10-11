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
            start = time.perf_counter()
            res = await device.read_screen_text(rect='[52,248,1028,2272]', lang='rus')
            print(res)

            end = time.perf_counter()
            print(end - start)
            res = await device.read_screen_text(rect='[52,248,1028,2272]', lang='eng')
            print(res)

            print(end - start)



if __name__ == '__main__':
    asyncio.run(main())