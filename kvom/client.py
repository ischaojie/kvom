from __future__ import annotations
from contextvars import ContextVar
from kvom.backends.base import ClientBackend, ConnPoolBackend
from kvom.backends.redis import RedisBackend

SUPPORTED_CLIENTS: dict[str, type[ClientBackend]] = {"redis": RedisBackend}


class ConnectionPool:
    def __init__(self, backend: ClientBackend) -> None:
        self.backend: ClientBackend = backend
        self.conn_pool: ConnPoolBackend = self.backend.pool()
        self.conn_count: int = 0

    def __enter__(self) -> ConnectionPool:
        self.conn_count += 1
        try:
            if self.conn_count == 1:
                self.conn_pool.acquire()
        except Exception as e:
            self.conn_count -= 1
            raise e
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        assert self.conn_count is not None
        self.conn_count -= 1
        if self.conn_count == 0:
            self.conn_pool.release()

    def get(self, key: bytes, default: bytes | None) -> bytes | None:
        return self.conn_pool.get(key, default)


class Client:
    def __init__(self) -> None:
        self.conn_ctx: ContextVar = ContextVar("conn_ctx")
        self.is_connected: bool = False
        self.backend = ClientBackend()

        self.connect()

    def connect(self) -> None:
        if self.is_connected:
            return None

        self.backend.conn_pool()
        self.is_connected = True

    def conn_pool(self) -> ConnectionPool:
        try:
            return self.conn_ctx.get()
        except LookupError:
            conn_pool = ConnectionPool(self.backend)
            self.conn_ctx.set(conn_pool)
            return conn_pool

    def get(self, key: bytes, default: bytes | None) -> bytes | None:
        with self.conn_pool() as conn_pool:
            return conn_pool.get(key, default)
