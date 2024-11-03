import asyncio
import time

from database.db import Device
from services.total_api import device_list


def get_center_bound(bound: list[int, int, int, int]) -> list[int, int]:
    return [int((bound[0] + bound[2]) / 2), int((bound[1] + bound[3]) / 2)]


async def main():
    devices = await device_list()
    print(devices)
    if devices:
        device = Device(devices[0])
        # res = await device.sendAai(params='{action:["getBounds"],query:"TP:more&&D:7"}')
        # bounds = res.get('value')['bounds']
        # print(bounds)
        # bound = bounds[0]
        # print(bound)
        # center_bound = get_center_bound(bound)
        # print(center_bound)
        res = await device.find_bound_from_query("TP:more&&D:7")
        print(res)
        for i in range(1, 5):
            res = await device.find_bound_from_query(f'R:otpPart{i}')
            cell1 = res
            print(cell1[0] / device.device_data.width * 100, cell1[1] / device.device_data.height * 100)
        # await device.click(res[0], res[1])
        # await device.click(res[0], res[1])
        # await device.click(res[0], res[1])
        # await device.click(res[0], res[1])

if __name__ == '__main__':
    asyncio.run(main())