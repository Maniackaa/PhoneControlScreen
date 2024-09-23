import asyncio
import datetime
import time

from config.bot_settings import logger as log
from database.db import Device
from services.func import wait_new_field, check_field
from services.total_api import device_list


async def card_data_input(device: Device, card, exp, cvv):
    """
    Ввод данных карты
    1. Жмем активации поля T:Заполните данные карты. Обновляем пока нет
    2. Вводим данные коля в первые редактируемые поля
    3. Жмем кнопку продолжить


    """
    logger = log.bind(step=1, device=device)
    logger.debug('Начат ввод данных карты:')
    is_ready = await check_field(device, '{query:"TP:more&&T:Заполните данные карты"}')
    while not is_ready:
        # await device.click(500, 1900)
        await device.input(code="recentapp")
        await asyncio.sleep(1)
        await device.input(code="recentapp")
        await asyncio.sleep(2)

        is_ready = await check_field(device, '{query:"TP:more&&T:Заполните данные карты"}')
    await asyncio.sleep(1)

    card_f = f'{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}'
    await device.sendAai(f'{{action: "setText({card_f})", query: "BP:editable&&IX:0"}}')
    await device.sendAai(f'{{action: "setText({exp})", query: "BP:editable&&IX:1"}}')
    await device.sendAai(f'{{action: "setText({cvv})", query: "BP:editable&&IX:2"}}')
    # await asyncio.sleep(1)

    # Клик на продолжить
    # res = await device.sendAai(params='{action:"click",query:"TP:more&&R:card-pay-btn"}' )
    res = await device.sendAai(params='{action:"click",query:"TP:more&&T:Оплатить"}')
    if res.get('value') == {'retval': True}:
        logger.info('Ввод данных карты завершен. Кнопка нажата')
    else:
        return 'unknown'

    # text = await device.read_screen_text()
    # text = text.get('value', '')
    # while 'Enter dynamic password' not in text:
    #     await asyncio.sleep(1)
    #     text = await device.read_screen_text()
    #     text = text.get('value', '')
    #
    # logger.info('Ввод данных карты завершен. Экран кода загружен')
    # return True


async def main():
    devices = await device_list()
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        await card_data_input(device, '4169738848626770', '06/27', '555')
        end = time.perf_counter()
        print(end - start)


if __name__ == '__main__':
    asyncio.run(main())
