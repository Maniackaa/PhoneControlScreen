import asyncio
import time

from database.db import Device
from services.total_api import device_list


async def main():
    devices = await device_list()
    print(devices)
    tasks = []
    for device_id in devices:
        device = Device(device_id)
        start = time.perf_counter()
        res = tasks.append(device.restart())
        end = time.perf_counter()
        print(end - start)
        print(res)
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())