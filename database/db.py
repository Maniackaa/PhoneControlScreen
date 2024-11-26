import asyncio
import base64
import dataclasses
import datetime
import json
import pickle
from enum import Enum

import aiohttp
import requests
import sqlalchemy
import structlog
from sqlalchemy import create_engine, ForeignKey, String, DateTime, \
    Integer, select, delete, Text, BLOB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database


# db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
from config.bot_settings import BASE_DIR, settings, logger

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
            setattr(self, key, value)
            _session.add(self)
            _session.commit()
            # logger.debug(f'Изменено значение {key} на {value}')
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


class DeviceStatus(Enum):
    UNKNOWN = 'Неизвестно'
    READY = 'Готовность'
    STEP0 = 'Назначен платеж'
    STEP1_0 = 'Шаг 1. Нажата кнопка TopUp'
    STEP1_1 = 'Шаг 1. Сумма введена'
    STEP1_2 = 'Шаг 1. Нажата кнопка далее'
    STEP2_0 = 'Шаг 2. На экране ввода карты'
    STEP2_1 = 'Шаг 2. Данные карты введены. Кнопка нажата'
    STEP3_0 = 'Шаг 3. Ожидание-Ввод кода'
    STEP3_1 = 'Шаг 3. Смс-код получен'
    STEP4_0 = 'Шаг 4. Ввод СМС'
    STEP4_1 = 'Шаг 4. На экране ввода смс'
    STEP4_2 = 'Шаг 4. Опознаны поля для ввода цифр'
    STEP4_3 = 'Шаг 4. Вставлены цифры смс'
    STEP4_4 = 'Шаг 4. Ожидание результата после ввода смс'
    STEP4_5 = 'Шаг 4. Финал'
    RESTART = 'Перезапуск'
    END = 'Скрипт отработал'


class DeviceData(Base):
    __tablename__ = 'device_data'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(50))
    width: Mapped[int] = mapped_column(Integer(), default=0)
    height: Mapped[int] = mapped_column(Integer(), default=0)
    manufacturer: Mapped[str] = mapped_column(String(50), nullable=True)
    device_name: Mapped[str] = mapped_column(String(50), nullable=True)
    device_status: Mapped[Enum] = mapped_column(sqlalchemy.Enum(
        DeviceStatus,     name="post_status_type",
        create_constraint=True,
        metadata=Base.metadata,
        validate_strings=True,))
    start_job_time: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    screen_text: Mapped[str] = mapped_column(Text(), nullable=True)
    last_screen_change: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)

    def __str__(self):
        return f'DeviceData({self.id}. {self.device_id}. {self.device_status})'


TOKEN = refresh_token()


def get_or_create_device_data(device_id) -> DeviceData:
    try:
        session = Session(expire_on_commit=False)
        with session:
            q = select(DeviceData).where(DeviceData.device_id == device_id).limit(1)
            device_data = session.execute(q).scalar_one_or_none()
            if not device_data:
                device_data = DeviceData(device_id=device_id, device_status=DeviceStatus.UNKNOWN)
                session.add(device_data)
                session.commit()
            return device_data

    except Exception as err:
        logger.error(f'Дата не создана: {err}', exc_info=True)


@dataclasses.dataclass
class Device:
    SMS_CODE_TIME_LIMIT = 190
    LEO_WAIT_LIMIT = 140

    device_id: str  # device@1021923620
    STEP2_END: datetime.datetime = None
    # status: Enum = DeviceStatus.UNKNOWN
    payment: dict = None

    @property
    def is_job_free(self) -> bool:
        # Проверяет есть ли задача с именем device_id
        all_task = asyncio.all_tasks(loop=None)
        for task in all_task:
            task_name = task.get_name()
            if task_name == self.device_data.device_id:
                return False
        return True

    @property
    def device_data(self) -> DeviceData:
        data = get_or_create_device_data(self.device_id)
        return data

    @property
    def timer(self) -> int:
        # Таймер показывает сколько прошло секунд от начала JOB
        device_data = get_or_create_device_data(self.device_id)
        if device_data.start_job_time:
            delta = (datetime.datetime.now() - device_data.start_job_time).total_seconds()
            return round(delta, 1)
        return 0

    def job_start(self):
        session = Session(expire_on_commit=False)
        with session:
            device_data = get_or_create_device_data(self.device_id)
            device_data.device_status = DeviceStatus.STEP0
            device_data.start_job_time = datetime.datetime.now()
            device_data.last_screen_change = datetime.datetime.now()
            session.add(device_data)
            session.commit()

    @property
    def start_job_time(self):
        device_data = get_or_create_device_data(self.device_id)
        return device_data.start_job_time

    @start_job_time.setter
    def start_job_time(self, value):
        session = Session(expire_on_commit=False)
        with session:
            device_data = get_or_create_device_data(self.device_id)
            old_value = device_data.start_job_time
            device_data.start_job_time = value
            session.add(device_data)
            session.commit()
            if old_value != value:
                logger.debug(f'Изменен счетчик таймера {self.device_id} на {value}')

    @property
    def device_status(self) -> DeviceStatus:
        device_data = get_or_create_device_data(self.device_id)
        return device_data.device_status

    @device_status.setter
    def device_status(self, status):
        session = Session(expire_on_commit=False)
        with session:
            device_data = get_or_create_device_data(self.device_id)
            old_status = device_data.device_status
            device_data.device_status = status
            session.add(device_data)
            session.commit()
            if old_status != status:
                logger.debug(f'Изменен статус {self.device_id} на {status}')

    async def check_timer(self):
        # Проверка не завис ли экран или не вышел ли таймер
        if self.start_job_time:
            if self.timer > settings.JOB_TIME_LIMIT:
                self.start_job_time = None
                raise asyncio.TimeoutError(self.device_id)

            # rect = '[52,248,1028,2272]'
            # lang = 'eng'
            # mode = 'multiline'
            # url = f'{self.device_url}/screen/texts?token={TOKEN}&rect={rect}&lang={lang}&mode={mode}'
            # device_data = self.device_data
            # delta = (datetime.datetime.now() - device_data.last_screen_change).total_seconds()
            # if delta > 10:
            #     async with aiohttp.ClientSession() as session:
            #         async with session.get(url) as response:
            #             if response.status == 200:
            #                 result = await response.json(content_type='application/json', encoding='UTF-8')
            #                 text = result.get('value', '')
            #                 old_text = self.device_data.screen_text
            #
            #                 if old_text == text:
            #                     # Текст не изменился
            #
            #                     print(f'Текст не менялся {delta}')
            #                     if delta > settings.SCREEN_TIME_LIMIT and self.start_job_time:
            #                         logger.warning(f'Завис более {settings.SCREEN_TIME_LIMIT} сек')
            #                         self.start_job_time = None
            #                         raise asyncio.TimeoutError(self.device_id)
            #                 else:
            #                     # Изменился
            #                     device_data.set('last_screen_change', datetime.datetime.now())
            #                     device_data.set('screen_text', text)

    @property
    def device_url(self) -> str:
        return f'http://localhost:8090/TotalControl/v2/devices/{self.device_id}'

    def logger(self):
        name = f'{self.device_id.split("@")[1]}'
        # processors = structlog.get_config()["processors"]
        # print(processors)
        # new_processors = processors[:-1] + [add_phone_name] + [processors[-1]]
        # structlog.configure(processors=new_processors)
        logger: structlog.stdlib.BoundLogger = structlog.get_logger(name, phone_name=f'{self.device_data.device_name}')
        # logger.info(f'Для {self} присвоен логгер {name}')
        return logger

    async def get_url(self, url, params=None, headers=None) -> dict:
        await self.check_timer()
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
        logger.debug(f'post_url: {url}')
        logger.debug(f'post_data: {data}')
        await self.check_timer()
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
                    self.logger().debug(f'{url} {response.status}')
                    if response.status == 200:
                        result = await response.json(content_type='application/json', encoding='UTF-8')
                        self.logger().debug(result)
                        return result
        except Exception as e:
            logger.error(e)
            raise e

    @property
    async def info(self):
        url = f'{self.device_url}?token={TOKEN}'
        result = await self.get_url(url)
        value = result.get('value', '')
        return value

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

    async def click_percent(self, x, y):
        x = int(x * self.device_data.width / 100)
        y = int(y * self.device_data.width / 100)
        res = await self.input(**{'x': x, 'y': y})
        return res

    async def click_on_field(self, field):
        q = f'{{action:"click",query:"{field}"}}'
        print(q)
        res = await self.sendAai(
                params=q
            )
        return res

    async def text(self, **kwargs):
        # Ввод текста
        self.logger().debug(f'text: {kwargs}')
        req_data = {"token": TOKEN,
                    **kwargs}
        print(req_data)
        url = f'{self.device_url}/screen/texts'
        res = await self.post_url(url, req_data)
        return res

    async def read_screen_text(self, rect='[1,10,99,90]', lang='eng', mode='multiline') -> str:
        """
        :param lang: ['eng', 'rus']
        :param rect: [x1,y1,x2,y2]
        :param mode
        : ['multiline', 'singleline']
        :return: {'status': True, 'value': "respose text\n"}
        """

        max_x = self.device_data.width
        max_y = self.device_data.height
        rect_list = json.loads(rect)
        rect = [
            int(rect_list[0] * max_x / 100),
            int(rect_list[1] * max_y / 100),
            int(rect_list[2] * max_x / 100),
            int(rect_list[3] * max_y / 100),
        ]
        result_rect = json.dumps(rect).replace(' ', '')
        url = f'{self.device_url}/screen/texts?token={TOKEN}&rect={result_rect}&lang={lang}&mode={mode}'
        res = await self.get_url(url)
        if lang == 'rus':
            self.logger().debug(json.dumps(res, ensure_ascii=False))
        else:
            self.logger().debug(json.dumps(res, ensure_ascii=True))

        return res.get('value', '')

    async def ready_response_check(self) -> bool:
        """
        Проверяет готовность ища поле D:Top up
        :return: bool
        """
        json_res = await self.sendAai(params='{query:"TP:more&&D:Top up"}')
        logger.debug(f'ready_response_check: {json_res}')
        value = json_res.get('value')
        if isinstance(value, dict):
            if value.get('count') == 1:
                return True
        return False

    async def db_ready_check(self) -> DeviceStatus:
        """
        Проверяет готовность по базе
        :return: Статус из БД
        """
        return self.device_status

    @staticmethod
    def get_center_bound(bound: list[int, int, int, int]) -> list[int, int]:
        return [int((bound[0] + bound[2]) / 2), int((bound[1] + bound[3]) / 2)]

    async def find_bound_from_query(self, query="TP:more&&D:7"):
        res = await self.sendAai(params=f'{{action:["getBounds"],query:"{query}"}}')
        print(res)
        result = res.get('value')
        if isinstance(result, dict):
            bounds = result.get('bounds')
            print(bounds)
            bound = bounds[0]
            print('bound:', bound, type(bound), len(bound))
            center_bound = self.get_center_bound(bound)
            print(center_bound)
            return center_bound

    async def restart(self):
        self.logger().debug('Выполняю перезапуск')
        self.device_status = DeviceStatus.RESTART
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
        coord_7 = await self.find_bound_from_query("TP:more&&D:7")
        # for i in '7777':
        #     await self.sendAai(params=f'{{action:"click",query:"TP:more&&D:{i}"}}')
        for i in range(4):
            await self.click(coord_7[0], coord_7[1])
            await asyncio.sleep(0.1)

        self.device_status = DeviceStatus.END

    async def alt_tab(self):
        # await self.input(code="recentapp")
        # await asyncio.sleep(1)
        # await self.input(code="recentapp")
        # await asyncio.sleep(1)
        await self.input(code="home")
        await asyncio.sleep(0.5)
        url = f'{self.device_url}/apps/com.m10?state=active&token={TOKEN}'
        res = await self.post_url(url)
        await asyncio.sleep(1)

    async def check_field(self, field):
        json_res = await self.sendAai(
            params=f'{{query:"{field}"}}'
        )
        value = json_res.get('value')
        if isinstance(value, dict):
            if value.get('count') == 1:
                return True
        return False


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)
