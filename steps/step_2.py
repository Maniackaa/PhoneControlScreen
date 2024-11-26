import asyncio
import datetime
import time

from database.db import Device, DeviceStatus
from services.func import wait_new_field, check_field
from services.total_api import device_list


async def card_data_input(device: Device, card, exp, cvv, log=None):
    """
    Ввод данных карты
    1. Жмем активации поля T:Заполните данные карты. Обновляем пока нет
    2. Вводим данные коля в первые редактируемые поля
    3. Жмем кнопку продолжить


    """
    if not log:
        log = device.logger()
    logger = log.bind(step=device.device_status)
    logger.debug('Начат ввод данных карты:')
    is_ready = await check_field(device, "TP:more&&T:Заполните данные карты")
    print(is_ready)
    while not is_ready:
        await device.alt_tab()
        is_ready = await check_field(device, "TP:more&&T:Заполните данные карты")
        await asyncio.sleep(1)
    card_f = f'{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}'
    await device.sendAai(f'{{action: "setText({card_f})", query: "BP:editable&&IX:0"}}')
    await device.sendAai(f'{{action: "setText({exp})", query: "BP:editable&&IX:1"}}')
    await device.sendAai(f'{{action: "setText({cvv})", query: "BP:editable&&IX:2"}}')
    # await asyncio.sleep(1)
    # Клик на продолжить
    # res = await device.sendAai(params='{action:"click",query:"TP:more&&R:card-pay-btn"}' )
    await device.sendAai(params='{action:"click",query:"TP:more&&T:Оплатить"}')
    await asyncio.sleep(3)
    await device.sendAai(params='{action:"click",query:"TP:more&&T:Оплатить"}')
    device.device_status = DeviceStatus.STEP2_1


async def main():
    devices = await device_list()
    if devices:
        device = Device(devices[0])
        start = time.perf_counter()
        await card_data_input(device, '5243754438854570', '09/29', '555')
        end = time.perf_counter()
        print(end - start)


if __name__ == '__main__':
    asyncio.run(main())
