from sys import stdout
from typing import Optional, Set

import humanize
from aiogram import types
from aiogram.bot.api import TELEGRAM_PRODUCTION, TelegramAPIServer
from aiogram.contrib.fsm_storage.redis import BaseStorage, RedisStorage2
from loguru import logger
from pydantic import AnyUrl, BaseSettings, RedisDsn

logger.remove()
humanize.i18n.activate("ru_RU")


class MongoDsn(AnyUrl):
    allowed_schemes = {"mongodb"}


class Settings(BaseSettings):
    logging_file: bool = False
    logging_rotation: str = "20 MB"
    logging_stdout: bool = True
    logging_level: str = "CRITICAL"

    telegram_token: str
    telegram_admins: Set[int] = set()

    bot_api_host: Optional[str] = None
    bot_api_port: Optional[int] = None

    webhook_url: Optional[str] = None
    webhook_path: Optional[str] = None
    webhook_port: Optional[int] = 8080
    webhook_host: Optional[str] = "0.0.0.0"
    health_check_path: Optional[str] = None

    mongo_dsn: MongoDsn = "mongodb://localhost:27017"
    mongo_db: str = "CraftBot"

    redis_dsn: RedisDsn = "redis://localhost:6379"
    redis_db_throttle: int = 1
    redis_db_bot: int = 1

    global_delay: int = 0.5
    TZ: str = "Europe/Moscow"

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        if self.logging_stdout:
            format_ = (
                "<green>{time:DD.MM.YY H:mm:ss}</green> "
                + " | <yellow><b>{level}</b></yellow> | <magenta>{file}:{function}:{line}</magenta> | <cyan>{message}</cyan>"
            )
            logger.add(
                stdout,
                colorize=True,
                format=format_,
                level=self.logging_level,
            )

        if self.logging_file:
            format_ = (
                "{time:DD.MM.YY H:mm:ss} "
                + " {level} {file}:{function}:{line} {message}"
            )
            logger.add(
                "logs/bot.log",
                rotation=self.logging_rotation,
                format=format_,
                level=self.logging_level,
            )

    @property
    def bot_id(self) -> int:
        return int(self.telegram_token.split(":")[0])

    @property
    def wh_max_connections(self) -> int:
        return 100000 if self.bot_api_host else 100

    @property
    def bot_api_server(self) -> TelegramAPIServer:
        if self.bot_api_host:
            host = f"http://{self.bot_api_host}"
            if self.bot_api_port:
                host += f":{self.bot_api_port}"
            return TelegramAPIServer.from_base(host)
        return TELEGRAM_PRODUCTION

    @property
    def is_polling(self) -> bool:
        return False if self.webhook_url and self.webhook_path else True

    @property
    def fsm_storage(self) -> BaseStorage:
        return RedisStorage2(
            host=self.redis_dsn.host,
            port=self.redis_dsn.port,
            db=self.redis_db_throttle,
            state_ttl=600,
            bucket_ttl=10,
            data_ttl=600,
            pool_size=100,
        )


# Any bot settings

allowed_updates = types.AllowedUpdates.MESSAGE | types.AllowedUpdates.CALLBACK_QUERY

cfg = Settings()
