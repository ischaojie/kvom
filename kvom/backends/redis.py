from __future__ import annotations
from redis import Redis, ConnectionPool
from kvom.backends.base import ClientBackend, PoolBackend


class RedisBackend(ClientBackend):
    def __init__(self, db_uri: str) -> None:
        self.db_uri = db_uri
        self.__pool = None

    def conn(self) -> None:


    def disconn(self) -> None:
        return super().disconn()

    def pool(self) -> RedisPool:
        pass


class RedisPool(PoolBackend):
    pass
