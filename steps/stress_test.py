import time

from database.db import Device
from config.bot_settings import logger


async def stress(device: Device):
    start = time.perf_counter()
    t = await device.read_screen_text()
    logger.bind(device_id=device.device_id)
    logger.info(t)
    end = time.perf_counter()
    print(round(end - start, 2))
    return t
