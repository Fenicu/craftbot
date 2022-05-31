import asyncio

import aioredis
from loguru import logger

from config import cfg


class FastRedis:
    def __init__(self):
        self._redis = None
        self._connection_lock = asyncio.Lock()

    async def get_db(self) -> aioredis.Redis:
        """
        Get redis connection db
        """
        async with self._connection_lock:
            if self._redis is None:
                logger.debug("Connection to {}", str(cfg.redis_dsn))
                self._redis = await aioredis.Redis(
                    host=cfg.redis_dsn.host,
                    port=cfg.redis_dsn.port,
                    db=cfg.redis_db_bot,
                    max_connections=100,
                    decode_responses=True,
                )
                await self._redis.ping()
                logger.debug("Connection successful")
        return self._redis

    async def close(self):
        if self._redis:
            return await self._redis.close()

    async def wait_closed(self):
        pass


redis = FastRedis()
