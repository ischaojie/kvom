# -*- coding: utf-8 -*-
import threading
from contextvars import ContextVar
from typing import Any, Dict, Union

from kvom.backend import DatabaseBackend, MemcachedBackend, RedisBackend
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

    def connect(self) -> None:
        if self.is_connected:
            return
        self._backend.connect()
        print("连上了")
        self.is_connected = True

    def disconnect(self) -> None:
        if not self.is_connected:
            return
        self._backend.disconnect()
        self.is_connected = False

    def connection(self) -> "Conn":
        try:
            return self._connection_context.get()
        except LookupError:
            conn = Conn(self._backend)
            self._connection_context.set(conn)
            return conn

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    def get(self, key: str) -> Any:
        with self.connection() as conn:
            return conn.get(key)

    def set(self, key: str, mapping: Dict) -> bool:
        with self.connection() as conn:
            return conn.set(key, mapping)

    def delete(self, key: str) -> bool:
        with self.connection() as conn:
            return conn.delete(key)


class Conn:
    def __init__(self, backend: DatabaseBackend) -> None:
        self._backend = backend
        self._conn = self._backend.connection()
        self._conn_lock = threading.Lock()
        self._conn_counter = 0

    def __enter__(self):
        with self._conn_lock:
            self._conn_counter += 1
            try:
                if self._conn_counter == 1:
                    self._conn.acquire()
            except BaseException as e:
                self._conn_counter -= 1
                raise e
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._conn_lock:
            assert self._conn is not None
            self._conn_counter -= 1
            if self._conn_counter == 0:
                self._conn.release()

    def get(self, key: str) -> Any:
        with self._conn_lock:
            return self._conn.get(key)

    def set(self, key: str, mapping: Dict) -> bool:
        with self._conn_lock:
            return self._conn.set(key, mapping)

    def delete(self, key: str) -> bool:
        with self._conn_lock:
            return self._conn.delete(key)
