



import asyncio
import time

from database.db import Device
from services.total_api import device_list


async def main():
    devices = await device_list()
    print(devices)
    sms_code = '2234'
    if devices:
        device = Device(devices[0])
        await device.sendAai(params=f'{{action:"setText({sms_code[0]})",query:"TP:more&&R:otpPart1"}}')
        await asyncio.sleep(0.5)
        await device.sendAai(params=f'{{action:"setText({sms_code[1]})",query:"TP:more&&R:otpPart2"}}')
        await asyncio.sleep(0.5)
        await device.sendAai(params=f'{{action:"setText({sms_code[2]})",query:"TP:more&&R:otpPart3"}}')
        await asyncio.sleep(0.5)
        await device.sendAai(params=f'{{action:"setText({sms_code[3]})",query:"TP:more&&R:otpPart4"}}')
        await asyncio.sleep(0.5)



if __name__ == '__main__':
    asyncio.run(main())