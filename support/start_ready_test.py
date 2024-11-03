import asyncio
import time

from database.db import Device
from services.total_api import device_list


async def main():
    devices = await device_list()
    print(devices)
    if devices:
        device = Device(devices[0])
        is_ready = await device.ready_response_check()
        print(is_ready)

if __name__ == '__main__':
    asyncio.run(main())