from typing import Optional

import pymongo.errors
from loguru import logger
from motor.core import AgnosticClient, AgnosticCollection, AgnosticDatabase
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from odmantic import AIOEngine

from config import cfg


class FastMongo:
    """
    Need to close Mongo client connections when shutdown
    await mongo.close()
    await mongo.wait_closed()
    """

    _db: Optional[AgnosticDatabase] = None
    _mongo: Optional[AgnosticClient] = None

    def get_client(self) -> AgnosticClient:
        if isinstance(self._mongo, AsyncIOMotorClient):
            return self._mongo
        try:
            logger.debug("Connection to {}", str(cfg.mongo_dsn))
            self._mongo: AgnosticClient = AsyncIOMotorClient(str(cfg.mongo_dsn))
        except pymongo.errors.ConfigurationError as e:
            if "query() got an unexpected keyword argument 'lifetime'" in e.args[0]:
                logger.warning(
                    "Run `pip install dnspython==1.16.0` in order to fix ConfigurationError. "
                    "More information: https://github.com/mongodb/mongo-python-driver/pull/423#issuecomment-528998245"
                )
            raise e
        return self._mongo

    def get_db(self) -> AgnosticDatabase:
        """
        Get mongo db
        """
        if isinstance(self._db, AsyncIOMotorDatabase):
            return self._db

        mongo = self.get_client()
        self._db = mongo.get_database(cfg.mongo_db)

        return self._db

    def get_coll(self, collection_name) -> AgnosticCollection:
        return self.get_db()[collection_name]

    async def close(self):
        if self._mongo:
            self._mongo.close()

    async def wait_closed(self):
        return True


class FastOdmanticMongo(FastMongo):
    """
    Need to close Mongo client connections when shutdown
    await mongo.close()
    await mongo.wait_closed()
    """

    _engine: Optional[AIOEngine] = None

    def get_engine(self) -> AIOEngine:
        if not self._engine:
            self._engine = AIOEngine(motor_client=self.get_client(), database=cfg.mongo_db)
        return self._engine


mongo = FastMongo()
odmantic_mongo = FastOdmanticMongo()
