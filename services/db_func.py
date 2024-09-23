from sqlalchemy import select

from config.bot_settings import logger
from database.db import DeviceData, Session, Device, DeviceStatus


def get_or_create_device_data(device: Device) -> DeviceData:
    try:
        session = Session(expire_on_commit=False)
        with session:
            q = select(DeviceData).where(DeviceData.device_id == device.device_id).limit(1)
            device_data = session.execute(q).scalar_one_or_none()
            print(device_data)
            if not device_data:
                device_data = DeviceData(device_id=device.device_id, device_status=DeviceStatus.UNKNOWN)
                session.add(device_data)
                session.commit()
            return device_data

    except Exception as err:
        logger.error(f'Дата не создана: {err}', exc_info=True)


# x = get_or_create_device_data(Device('device@1021923620'))
# print(x)


