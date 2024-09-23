import asyncio
import base64
import dataclasses
import datetime
import json
import pickle
from enum import Enum

import aiohttp
import requests
from sqlalchemy import create_engine, ForeignKey, String, DateTime, \
    Integer, select, delete, Text, BLOB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database


# db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
from config.bot_settings import BASE_DIR, logger, settings


db_path = BASE_DIR / 'base.sqlite'
db_url = f"sqlite:///{db_path}"
engine = create_engine(db_url, echo=False)
Session = sessionmaker(bind=engine)


def refresh_token():
    s = f'{settings.TOTAL_LOGIN}:{settings.TOTAL_PASSWORD}'
    userpass = base64.b64encode(s.encode('utf-8'))
    if userpass:
        url = "http://localhost:8090/TotalControl/v2/login"
        headers = {
            'Authorization': userpass
        }
        res = requests.get(url, headers=headers)
        print('login:', res.text)
        if res.text:
            parsed_data = json.loads(res.text)
            token = parsed_data['value']['token']
            print('token:', token)
            if token:
                return token


class Base(DeclarativeBase):
    def set(self, key, value):
        _session = Session(expire_on_commit=False)
        with _session:
            if isinstance(value, str):
                value = value[:999]
            setattr(self, key, value)
            _session.add(self)
            _session.commit()
            logger.debug(f'Изменено значение {key} на {value}')
            return self


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    tg_id: Mapped[str] = mapped_column(String(30), unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    register_date: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    fio: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer(), default=0)

    def __repr__(self):
        return f'{self.id}. {self.username or "-"} {self.tg_id}'


TOKEN = refresh_token()


class DeviceStatus(Enum):
    READY = 'Готовность'
    STEP1 = 'Шаг 1. Ввод суммы'
    STEP2 = 'Шаг 2. Ввод данных карты'
    STEP3 = 'Шаг 3. Ожидание-Ввод кода'


@dataclasses.dataclass
class Device:
    SMS_CODE_TIME_LIMIT = 180

    device_id: str  # device@1021923620
    STEP2_END: datetime.datetime = None
    status: Enum = DeviceStatus.READY

    @property
    def device_url(self):
        return f'http://localhost:8090/TotalControl/v2/devices/{self.device_id}'

    def logger(self):
        return logger.bind(device_id=self.device_id)


    async def get_url(self, url, params=None, headers=None) -> dict:
        if headers is None:
            headers = {}
        if params is None:
            params = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url,
                                   headers=headers,
                                   params=params) as response:
                if response.status == 200:
                    result = await response.json(content_type='application/json', encoding='UTF-8')
                    return result

    async def post_url(self, url, data=None, headers=None) -> dict:
        if headers is None:
            headers = {}
        if data is None:
            data = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url,
                                        headers=headers,
                                        data=data
                                        ) as response:
                    if response.status == 200:
                        result = await response.json(content_type='application/json', encoding='UTF-8')
                        return result
        except Exception as e:
            logger.error(e)
            raise e

    async def sendAai(self, params):
        req_data = {"token": TOKEN,
                    'params': params}
        url = f'{self.device_url}/sendAai'
        res = await self.post_url(url, data=req_data)
        self.logger().debug(f'sendAai {params}: {res}')
        return res

    async def input(self, **kwargs):
        req_data = {"token": TOKEN,
                    **kwargs}
        url = f'{self.device_url}/screen/inputs'
        res = await self.post_url(url, data=req_data)
        self.logger().debug(f'input {kwargs}: {res}')
        return res

    async def click(self, x, y):
        res = await self.input(**{'x': x, 'y': y})
        return res

    async def text(self, **kwargs):
        self.logger().debug(f'text: {kwargs}')
        req_data = {"token": TOKEN,
                    **kwargs}
        url = f'{self.device_url}/screen/texts'
        res = await self.post_url(url, req_data)
        return res

    async def read_screen_text(self, rect='[52,248,1028,2272]', lang='eng', mode='multiline') -> dict:
        """
        :param lang: ['eng', 'rus']
        :param mode: ['multiline', 'singleline']
        :return: {'status': True, 'value': "respose text\n"}
        """
        url = f'{self.device_url}/screen/texts?token={TOKEN}&rect={rect}&lang={lang}&mode={mode}'
        res = await self.get_url(url)
        self.logger().debug(res)
        return res

    async def restart(self):
        url = f'{self.device_url}/apps/com.m10?state=restart&token={TOKEN}'
        res = await self.post_url(url)
        if not res:
            return False
        value = None
        while not isinstance(value, dict):
            json_res = await self.sendAai(params='{query:"TP:all&&D:7"}')
            value = json_res.get('value')
            if isinstance(value, dict):
                if value.get('count') == 1:
                    break
            self.logger().debug('Ждем панель')
            await asyncio.sleep(1)
        await asyncio.sleep(1)
        for i in '7777':
            res = await self.sendAai(params=f'{{action:"click",query:"TP:more&&D:{i}"}}')

        await asyncio.sleep(1)


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)
