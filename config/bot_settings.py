import logging
from functools import lru_cache
from pathlib import Path
from pprint import pprint
from typing import List

import pytz as pytz
import structlog
import logging.config
from pydantic_settings import BaseSettings, SettingsConfigDict
from structlog.stdlib import AsyncBoundLogger
from structlog.typing import WrappedLogger, EventDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # BOT_TOKEN: str  # Токен для доступа к телеграм-боту
    # ADMIN_IDS: list  # Список id администраторов бота
    BASE_DIR: Path = BASE_DIR
    TIMEZONE: str = "Europe/Moscow"
    USE_REDIS: bool = False
    LOG_TO_FILE: bool = False
    # EMAIL_HOST_USER: str
    # EMAIL_HOST_PASSWORD: str
    # SERVER_EMAIL: str
    # EMAIL_PORT: int
    TOTAL_LOGIN: str
    TOTAL_PASSWORD: str
    ASUPAY_LOGIN: str
    ASUPAY_PASSWORD: str
    ASU_HOST: str
    JOB_TIME_LIMIT: int
    SCREEN_TIME_LIMIT: int
    LOG_LEVEL: str = 'DEBUG'
    PHONES: List[str] = []

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")

    @property
    def tz(self):
        return pytz.timezone(self.TIMEZONE)


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()

timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False)
pre_chain = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.ExtraAdder(),
    timestamper,
]


def extract_from_record(_, __, event_dict):
    """
    Extract thread and process names and add them to the event dict.
    """
    record = event_dict["_record"]
    # event_dict["thread_name"] = record.threadName
    # event_dict["process_name"] = record.processName
    return event_dict


device_ids = settings.PHONES
print(device_ids)
LOG_PATH = BASE_DIR / 'logs'

handlers = {
    "console": {
        "level": f"{settings.LOG_LEVEL}",
        "class": "logging.StreamHandler",
        "formatter": "colored",
    },
    "console_file": {
        "level": "DEBUG",
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": LOG_PATH / "console_file.log",
        "formatter": "plain",
        'when': 'h',
        'interval': 1,
        'backupCount': 24 * 30
    },
    "file": {
        "level": "DEBUG",
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": LOG_PATH / "script.log",
        "formatter": "plain",
        'when': 'h',
        'interval': 1,
        'backupCount': 24 * 30
    },
}

loggers = {"main": {"handlers": ["console", "console_file", "file"],
                    "level": "DEBUG",
                    "propagate": True,
                    },
           }

for device_id in device_ids:
    handlers[device_id] = {
        "level": "DEBUG",
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": LOG_PATH / f"{device_id}.log",
        'when': 'h',
        'interval': 1,
        'backupCount': 24 * 30,
        # "formatter": "colored",
        "formatter": "plain",
    }

    loggers[device_id] = {"handlers": [f"{device_id}"],
                          "level": "DEBUG",
                          "propagate": True,
                          }

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    # structlog.dev.ConsoleRenderer(colors=False),
                    structlog.processors.JSONRenderer(ensure_ascii=True)
                ],
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    extract_from_record,
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": handlers,
        "loggers": loggers,

    }
)


def add_phone_name(a, b, event_dict):

    if 'phone_name' in event_dict.keys():
        phone_label = f"-{event_dict.get('phone_name', ''):2}-"
        if event_dict.get('event'):
            event_dict['event'] = f"{phone_label} {event_dict['event']}"
    return event_dict


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        # structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        # structlog.processors.TimeStamper(fmt="iso"),
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # If some value is in bytes, decode it to a Unicode str.
        # structlog.processors.UnicodeDecoder(),
        # structlog.processors.UnicodeEncoder(),
        # Add callsite parameters.
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
                # structlog.processors.CallsiteParameter.PATHNAME ,
                # structlog.processors.CallsiteParameter.MODULE,
                # structlog.processors.CallsiteParameter.PROCESS,
                # structlog.processors.CallsiteParameter.PROCESS_NAME,
                # structlog.processors.CallsiteParameter.THREAD,
                # structlog.processors.CallsiteParameter.THREAD_NAME
            }
        ),
        # structlog.processors.JSONRenderer(),
        structlog.stdlib.ExtraAdder(),
        add_phone_name,
        structlog.dev.ConsoleRenderer(colors=True),
        # structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    # wrapper_class=AsyncBoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger('main')
logger.info('Логгер OK')

# pprint({
#         "version": 1,
#         "disable_existing_loggers": False,
#         "formatters": {
#             "plain": {
#                 "()": structlog.stdlib.ProcessorFormatter,
#                 "processors": [
#                     structlog.stdlib.ProcessorFormatter.remove_processors_meta,
#                     structlog.dev.ConsoleRenderer(colors=False),
#                 ],
#                 "foreign_pre_chain": pre_chain,
#             },
#             "colored": {
#                 "()": structlog.stdlib.ProcessorFormatter,
#                 "processors": [
#                     extract_from_record,
#                     structlog.stdlib.ProcessorFormatter.remove_processors_meta,
#                     structlog.dev.ConsoleRenderer(colors=True),
#                 ],
#                 "foreign_pre_chain": pre_chain,
#             },
#         },
#         "handlers": handlers,
#         "loggers": loggers,
#
#     })

logger.info("Манат 'MANAT SIGN' (U+20BC) ₼")