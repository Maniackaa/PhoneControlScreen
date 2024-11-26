import asyncio
import time

from database.db import Device
from services.total_api import device_list
field_query = "TP:more&&R:Callback_sms"
sms_code = '1234'
# {action:"setText(1234)",query:"TP:more&&R:psw_id"}

async def input_text_in_field(device, text: str, field: str):
    # '{{action:"setText({sms_code})",query:"{field_query}"}}'
    params = f'{{action:"setText({sms_code})",query:"{field}"}}'
    res = await device.sendAai(params=params)
    print(res)



async def main():
    devices = await device_list()
    print(devices)
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        q1 = f'{{action:"setText({sms_code})",query:"{field_query}"}}'
        q2 = f'{{action:"setText({sms_code})",{field_query}}}'
        print(q1)
        print(q2)
        await device.sendAai(params=q1)
        end = time.perf_counter()
        print(end - start)
        # print(res)


if __name__ == '__main__':
    asyncio.run(main())