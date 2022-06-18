from support.dbmanager.FastMongo import (FastMongo, FastOdmanticMongo, mongo,
                                         odmantic_mongo)
from support.dbmanager.FastRedis import FastRedis, redis

__all__ = [
    "mongo",
    "odmantic_mongo",
    "FastMongo",
    "FastOdmanticMongo",
    "redis",
    "FastRedis",
]
