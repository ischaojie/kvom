# -*- coding: utf-8 -*-
import asyncio
from contextvars import ContextVar
from typing import Union, Any, Dict

from kvom.backend import DatabaseBackend, RedisBackend, MemcachedBackend
from kvom.utils import DatabaseURL


class Database:
    SUPPORTED_BACKENDS = {
        "redis": RedisBackend,
        "memcached": MemcachedBackend,
    }

    def __init__(
        self,
        url: Union[str, DatabaseURL],
        **options: Any,
    ):
        self.url = DatabaseURL(url)
        self.options = options
        self.is_connected = False
        self._backend = self.SUPPORTED_BACKENDS.get(
            self.url.scheme, self.SUPPORTED_BACKENDS[self.url.dialect]
        )(self.url, **self.options)

        self._connection_context = ContextVar("connection_context")  # type: ContextVar

    async def connect(self) -> None:
        if self.is_connected:
            return None

        await self._backend.connect()

        self.is_connected = True

    async def disconnect(self) -> None:
        if not self.is_connected:
            return
        await self._backend.disconnect()
        self.is_connected = False

    def connection(self) -> "Conn":
        try:
            return self._connection_context.get()
        except LookupError:
            _conn = Conn(self._backend)
            self._connection_context.set(_conn)
            return _conn

    async def __aenter__(self) -> "Database":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def get(self, key: str) -> Any:
        async with self.connection() as conn:
            return await conn.get(key)

    async def set(self, key: str, mapping: Dict) -> bool:
        async with self.connection() as conn:
            return await conn.set(key, mapping)

    async def delete(self, key: str) -> bool:
        async with self.connection() as conn:
            return await conn.delete(key)


class Conn:
    def __init__(self, backend: DatabaseBackend) -> None:
        self._backend = backend
        self._conn = self._backend.connection()
        self._conn_lock = asyncio.Lock()
        self._conn_counter = 0

    async def __aenter__(self):
        async with self._conn_lock:
            self._conn_counter += 1
            try:
                if self._conn_counter == 1:
                    await self._conn.acquire()
            except BaseException as e:
                self._conn_counter -= 1
                raise e
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._conn_lock:
            assert self._conn is not None
            self._conn_counter -= 1
            if self._conn_counter == 0:
                await self._conn.release()

    async def get(self, key: str) -> Any:
        async with self._conn_lock:
            return await self._conn.get(key)

    async def set(self, key: str, mapping: Dict) -> bool:
        async with self._conn_lock:
            return await self._conn.set(key, mapping)

    async def delete(self, key: str) -> bool:
        async with self._conn_lock:
            return await self._conn.delete(key)
