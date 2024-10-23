import asyncio
import time

from database.db import Device
from services.total_api import device_list


async def main():
    devices = await device_list()
    print(devices)
    if devices:
        device = Device(devices[0])
        print(device)
        sms_code = '1234'
        await device.click(150, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[0]}')

        await device.click(400, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[1]}')

        await device.click(680, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[2]}')

        await device.click(950, 920)
        await asyncio.sleep(1)
        await device.text(text=f'{sms_code[3]}')


if __name__ == '__main__':
    asyncio.run(main())
