# -*- coding: utf-8 -*-
from typing import Any, Union, Dict

from kvom.utils import DatabaseURL
from aioredis.connection import ConnectionPool as RedisConnPool


class DatabaseBackend:
    async def connect(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    async def disconnect(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def connection(self) -> "ConnBackend":
        raise NotImplementedError()  # pragma: no cover


class ConnBackend:
    async def acquire(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    async def release(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    async def get(self, key: str) -> Any:
        raise NotImplementedError()  # pragma: no cover

    async def set(self, key: str, mapping: Dict) -> bool:
        raise NotImplementedError()  # pragma: no cover

    async def delete(self, key: str) -> bool:
        raise NotImplementedError()  # pragma: no cover


class RedisBackend(DatabaseBackend):
    def __init__(self, url: Union[str, "DatabaseURL"], **options: Any) -> None:
        self._url = DatabaseURL(url)
        self._options = options
        self._pool = None

    async def connect(self) -> None:
        assert self._pool is None, "DatabaseBackend is already running"
        keywords = {
            "host": self._url.hostname,
            "port": self._url.port,
            "db": self._url.database,
        }
        keywords.update(**self._options)
        pool = RedisConnPool(**keywords)
        await pool.get_connection("_")
        self._pool = pool

    async def disconnect(self) -> None:
        assert self._pool is not None, "DatabaseBackend is not running"
        await self._pool.disconnect()
        self._pool = None

    def connection(self) -> "RedisConn":
        return RedisConn(self)


class RedisConn(ConnBackend):
    def __init__(self, database: RedisBackend) -> None:
        self._database = database
        self._conn = None

    async def acquire(self) -> None:
        assert self._conn is None, "Connection is already acquired"
        assert self._database._pool is not None, "DatabaseBackend is not running"
        self._conn = await self._database._pool.get_connection("_")

    async def release(self) -> None:
        assert self._conn is not None, "Connection is not acquired"
        assert self._database._pool is not None, "DatabaseBackend is not running"
        self._conn = await self._database._pool.disconnect()
        self._conn = None

    async def get(self, key: str) -> Any:
        return await self._conn.send_command("HGETALL", key)

    async def set(self, key: str, mapping: Dict) -> bool:
        """redis use hashset to set"""
        items = []
        for pair in mapping.items():
            items.extend(pair)
        return await self._conn.send_command("HSET", key, *items)

    async def delete(self, key: str) -> bool:
        pass


class MemcachedBackend(DatabaseBackend):
    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    def connection(self) -> "ConnBackend":
        pass
