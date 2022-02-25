# -*- coding: utf-8 -*-
from typing import Any, Union, Dict

from kvom.utils import DatabaseURL
from redis.connection import ConnectionPool as RedisConnPool


class DatabaseBackend:
    def connect(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def disconnect(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def connection(self) -> "ConnBackend":
        raise NotImplementedError()  # pragma: no cover


class ConnBackend:
    def acquire(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def release(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def get(self, key: str) -> Any:
        raise NotImplementedError()  # pragma: no cover

    def set(self, key: str, mapping: Dict) -> bool:
        raise NotImplementedError()  # pragma: no cover

    def delete(self, key: str) -> bool:
        raise NotImplementedError()  # pragma: no cover


class RedisBackend(DatabaseBackend):
    def __init__(self, url: Union[str, "DatabaseURL"], **options: Any) -> None:
        self._url = DatabaseURL(url)
        self._options = options
        self._pool = None

    def connect(self) -> None:
        keywords = {
            "host": self._url.hostname,
            "port": self._url.port,
            "db": self._url.database,
        }
        keywords.update(**self._options)
        self._pool = RedisConnPool(**keywords)

    def disconnect(self) -> None:
        assert self._pool is not None, "DatabaseBackend is not running"
        self._pool.disconnect()
        self._pool = None

    def connection(self) -> "RedisConn":
        try:
            self.connect()
        except Exception as e:
            raise e

        return RedisConn(self)


class RedisConn(ConnBackend):
    def __init__(self, database: RedisBackend) -> None:
        self._database = database
        self._conn = None

    def acquire(self) -> None:
        self._conn = self._database._pool.get_connection("_")

    def release(self) -> None:
        assert self._conn is not None, "Connection is not acquired"
        assert self._database._pool is not None, "DatabaseBackend is not running"
        self._conn = self._database._pool.release(self._conn)
        self._conn = None

    def get(self, key: str) -> Any:
        return self._conn.send_command("HGETALL", key)

    def set(self, key: str, mapping: Dict) -> bool:
        """redis use hashset to set"""
        items = []
        for pair in mapping.items():
            items.extend(pair)
        return self._conn.send_command("HSET", key, *items)

    def delete(self, key: str) -> bool:
        pass


class MemcachedBackend(DatabaseBackend):
    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def connection(self) -> "ConnBackend":
        pass
