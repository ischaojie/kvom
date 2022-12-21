from __future__ import annotations
from contextvars import ContextVar
from kvom.backends.base import ClientBackend, PoolBackend


class Pool:
    def __init__(self, backend: ClientBackend) -> None:
        self.__backend: ClientBackend = backend
        self.__conn: PoolBackend = self.__backend.pool()
        self.__conn_count: int = 0

    def __enter__(self) -> Pool:
        self.__conn_count += 1
        try:
            if self.__conn_count == 1:
                self.__conn.acquire()
        except Exception as e:
            self.__conn_count -= 1
            raise e
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        assert self.__conn_count is not None
        self.__conn_count -= 1
        if self.__conn_count == 0:
            self.__conn.release()

    def get(self, key: bytes, default: bytes | None) -> bytes | None:
        return self.__conn.get(key, default)


class Client:
    SUPPORTED_CLIENTS = {
        "redis": "kvom.backends.redis.RedisClient",
    }

    def __init__(self) -> None:
        self.__conn_ctx: ContextVar = ContextVar("conn_ctx")
        self.is_connected: bool = False
        self.__backend = ClientBackend()

        self.__connect()

    def __connect(self) -> None:
        if self.is_connected:
            return None

        self.__backend.conn()
        self.is_connected = True

    def conn(self) -> Pool:
        try:
            return self.__conn_ctx.get()
        except LookupError:
            conn = Pool(self.__backend)
            self.__conn_ctx.set(conn)
            return conn

    def get(self, key: bytes, default: bytes | None) -> bytes | None:
        with self.conn() as conn:
            return conn.get(key, default)
