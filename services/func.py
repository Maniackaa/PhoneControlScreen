import asyncio
import dataclasses
import time
from pathlib import Path

import pyautogui
import cv2
import time
import numpy as np

from config.bot_settings import logger
from database.db import Device

data = "10;5402691959414698;08/25;299;3434"
amount, card, exp, cvv, sms = data.split(';')


@dataclasses.dataclass
class Target:
    img: Path
    x: int
    y: int


def find_target_in_image(screenshot, target: Target, treshold=0.8):
    target_pic = cv2.imread(target.img.as_posix())
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    res = cv2.matchTemplate(screenshot_bgr, target_pic, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= treshold)
    pairs = list(zip(*loc[::-1]))
    if pairs:
        x, y = pairs[-1][0], pairs[-1][1]
        return x + target.x, y + target.y


def make_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save('scr.png')
    return screenshot


async def check_field(device, params) -> bool:
    """Ишем есть ли поле
    :param device:
    :param params: '{query:"TP:more&&R:cardPan"}'
    :return:
    """

    json_res = await device.sendAai(
        params=params
    )
    value = json_res.get('value')
    if isinstance(value, dict):
        if value.get('count') == 1:
            return True
    return False


async def check_bad_result(device: Device, text_rus=None, text_eng=None) -> str:
    """
    Проверяет признаки плохого платежа: тексты неверный, wrong, failed и поле D:Transaction failed
    :param device:
    :param text_rus:
    :param text_eng:
    :return: None / 'decline. restart' / 'decline'
    """
    if not text_rus:
        text_rus = await device.read_screen_text(lang='rus')
    if not text_eng:
        text_eng = await device.read_screen_text(lang='eng')
    log = logger.bind(device_id=device.device_id)
    payment_result = ''
    is_failed = await check_field(device, params='{query:"TP:all&&D:Transaction failed"}')
    if is_failed:
        log.info('Найдено поле Transaction failed')
        payment_result = 'decline'
    is_incorrect = 'неверный' in text_rus.lower() or 'wrong' in text_eng.lower() or 'failed' in text_eng.lower()
    if is_incorrect:
        logger.info('Найдено поле Неверный срок или Неверный номер')
        payment_result = 'decline. restart'
    return payment_result


async def wait_new_field(device, params, limit=60):
    # Ждем поле
    is_ready = False
    count = 0
    is_ready = await check_field(device, params)
    while not is_ready:
        await device.input(code="recentapp")
        await asyncio.sleep(1)
        await device.input(code="recentapp")
        await asyncio.sleep(2)
        is_ready = await check_field(device, params)
    return True





async def get_card_data():
    return '1;5462631218826164;08/25;299;3434'
