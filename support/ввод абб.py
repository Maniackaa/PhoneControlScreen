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
        res = await device.sendAai(params=f'{{action:"setText({1234})",query:"TP:more&&R:psw_id"}}')
        print(res)
        res = await device.click_field('R:btnSubmit')
        end = time.perf_counter()
        print(end - start)
        print(res)


if __name__ == '__main__':
    asyncio.run(main())