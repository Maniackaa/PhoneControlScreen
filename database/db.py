import base64
import dataclasses
import datetime
import json
import pickle

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


@dataclasses.dataclass
class Device:
    device_id: str  # device@1021923620

    @property
    def device_url(self):
        return f'http://localhost:8090/TotalControl/v2/devices/{self.device_id}'

    async def sendAai(self, params):
        logger.debug('sendAai', params=params)
        req_data = {"token": TOKEN,
                    'params': params}
        res = requests.post(f'{self.device_url}/sendAai', json.dumps(req_data))
        return res

    async def input(self, **kwargs):
        req_data = {"token": TOKEN,
                    **kwargs}
        res = requests.post(f'{self.device_url}/screen/inputs', json.dumps(req_data))
        return res

    async def text(self, **kwargs):
        req_data = {"token": TOKEN,
                    **kwargs}
        res = requests.post(f'{self.device_url}/screen/texts', json.dumps(req_data))
        return res

    async def read_screen_text(self, rect, lang, mode):
        url = f'{self.device_url}/screen/texts?token={TOKEN}&rect={rect}&lang={lang}&mode={mode}'
        res = requests.get(url)
        return res.json().get('value', '')


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)
