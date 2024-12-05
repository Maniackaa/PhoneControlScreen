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
        # res = await device.click_on_field('TP:more&&D:Пополнить')
        # await device.sendAai(params=f'{{action:"setText({2})",query:"TP:more&&R:otpPart1"}}')
        # res = await device.click(12, 39)
        # await device.click(int(50 * device.device_data.width / 100), int(50 * device.device_data.height / 100))
        #37.3 48.68
        ratio = device.device_data.width / device.device_data.height
        print(f'ratio: {ratio}')
        # 0.47368421052631576
        if ratio == 0.45:
            print(0.45)
            y_input = 32
            y_confirm = 39
        else:
            print(f'не 45')
            y_input = 37.2
            y_confirm = 48.68
        x_coord = 40
        print(x_coord, y_input, y_confirm)
        x = int(x_coord * device.device_data.width / 100)
        y = int(y_input * device.device_data.height / 100)
        await device.click(x, y)

        # x = int(x_coord * device.device_data.width / 100)
        # y = int(y_confirm * device.device_data.height / 100)
        # await device.click(x, y)
        await asyncio.sleep(1)
        end = time.perf_counter()
        print(end - start)
        # print(res)


if __name__ == '__main__':
    asyncio.run(main())