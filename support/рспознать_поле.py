import asyncio
import time

from database.db import Device
from services.func import check_field
from services.total_api import device_list
field_query = "TP:more&&D:Top up"
sms_code = '1234'
# {action:"setText(1234)",query:"TP:more&&R:psw_id"}
async def main():
    devices = await device_list()
    print(devices)
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        is_ready = await check_field(device, "TP:more&&D:Top-up wallet")
        print(is_ready)
if __name__ == '__main__':
    asyncio.run(main())