import asyncio
import time

from database.db import Device
from services.total_api import device_list


async def main():
    devices = await device_list()
    print(devices)
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        # res = await device.input(**{'x': '200', 'y': '1000'})
        res = await device.click_on_field('TP:more&&D:Top up')
        end = time.perf_counter()
        print(end - start)
        print(res)


if __name__ == '__main__':
    asyncio.run(main())