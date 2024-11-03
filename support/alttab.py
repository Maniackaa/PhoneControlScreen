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
        await device.alt_tab()
        end = time.perf_counter()
        print(end - start)


if __name__ == '__main__':
    asyncio.run(main())