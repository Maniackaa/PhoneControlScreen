import asyncio
import time

from database.db import Device
from services.total_api import device_list
field_query = "TP:more&&D:Top up"
field_query = "T:Подтвердить"
sms_code = '1234'
# {action:"setText(1234)",query:"TP:more&&R:psw_id"}
async def main():
    devices = await device_list()
    print(devices)
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        res = await device.check_field(field_query)
        print(res)
        end = time.perf_counter()
        print(end - start)
        # print(res)


if __name__ == '__main__':
    asyncio.run(main())