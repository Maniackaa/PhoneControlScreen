import asyncio
import datetime

import time
from config.bot_settings import logger as log
from database.db import Device, DeviceStatus

from services.total_api import device_list


async def stress_job(device: Device):
    while True:
        start = time.perf_counter()
        await asyncio.sleep(0.5)
        await device.read_screen_text()
        print(f'Паралельная Общее время: {time.perf_counter() - start} c.')


async def main():
    while True:
        try:
            devices_ids = await device_list() or []
            for num, device_id in enumerate(devices_ids, 1):
                device = Device(device_id)
                asyncio.create_task(stress_job(device))
                start = time.perf_counter()
                await device.read_screen_text()
                print(f'Main Общее время: {time.perf_counter() - start} c.')
            await asyncio.sleep(1)
        except Exception as err:
            log.error(err)
            await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        input('Enter')