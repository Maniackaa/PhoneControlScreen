import asyncio
import aiohttp

import time
from config.bot_settings import logger as log
from database.db import Device

from services.total_api import device_list


# async def get_url(self, url) -> dict:
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url) as response:
#             if response.status == 200:
#                 result = await response.json(content_type='application/json', encoding='UTF-8')
#                 return result

# async def read_screen_text(self, rect='[52,248,1028,2272]', lang='eng', mode='multiline') -> str:
#     url = f'{self.device_url}/screen/texts?token={TOKEN}&rect={rect}&lang={lang}&mode={mode}'
#     res = await self.get_url(url)
#     return res.get('value', '')

async def stress_job(device: Device):
    while True:
        start = time.perf_counter()
        await asyncio.sleep(0.5)
        await device.read_screen_text()
        print(f'Parralel: {time.perf_counter() - start} c.')


async def main():
    while True:
        try:
            devices_ids = await device_list() or []
            for num, device_id in enumerate(devices_ids, 1):
                device = Device(device_id)
                asyncio.create_task(stress_job(device))
                start = time.perf_counter()
                await device.read_screen_text()
                print(f'Main total time: {time.perf_counter() - start} c.')
            await asyncio.sleep(1)
        except Exception as err:
            log.error(err)
            await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        log.error(err)
        input()
