import asyncio
import time

from database.db import Device
from services.total_api import device_list
from steps.stress_test import stress


async def main():
    while True:
        devices = await device_list()
        for device in devices:
            device = Device(device)
            if device:
                task = asyncio.create_task(stress(device))
                # res = await task
                # print(res)
                # print(device.device_id, repr(res.get('value')))
        print('---------------------------------')
        print()
        await asyncio.sleep(0.8)

if __name__ == '__main__':
    asyncio.run(main())