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
        balance_field = await device.sendAai(params='{action:"getDescription",query:"TP:more&&D:Available balance&&OY:1"}')
        if balance_field['status'] == True:
            balance_raw = balance_field['value']['retval']
            print(balance_raw)
        print(time.perf_counter() - start)
        b = await device.get_raw_balance()
        print(b)
if __name__ == '__main__':
    asyncio.run(main())