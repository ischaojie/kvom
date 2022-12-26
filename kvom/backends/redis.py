from __future__ import annotations
from redis import ConnectionPool, Connection
from redis.exceptions import ResponseError
from kvom.backends.base import ClientBackend, ConnPoolBackend


class RedisBackend(ClientBackend):
    def __init__(self, db_uri: str) -> None:
        self.db_uri = db_uri
        self._conn_pool: ConnectionPool | None = None

    def conn(self) -> None:
        assert self._conn_pool is None, "ClientBackend is already running"
        self._conn_pool = ConnectionPool.from_url(self.db_uri)

    def disconn(self) -> None:
        if self._conn_pool is None:
            return
        self._conn_pool.disconnect()
        self._conn_pool = None

    def conn_pool(self) -> RedisConnPool:
        return RedisConnPool(self)


class RedisConnPool(ConnPoolBackend):
    def __init__(self, db: RedisBackend) -> None:
        self.db = db
        self.conn: Connection | None = None

    def acquire(self) -> None:
        assert self.conn is None, "conn_pool is already acquired"
        assert self.db.conn_pool is not None, "ClientBackend is not running"
        self.conn = self.db.conn_pool.make_conn()

    def release(self) -> None:
        assert self.conn is not None, "conn_pool is not acquired"
        assert self.db.conn_pool is not None, "ClientBackend is not running"
        self.db.conn_pool.release(self.conn)

    def execute_command(self, *args, **options):
        """Execute a command and return a parsed response"""
        command_name = args[0]
        try:
            self.conn.send_command(*args)
            return self.parse_response(self.conn, command_name, **options)
        finally:
            if not self.conn:
                self.db.conn_pool.release(self.conn)

    def parse_response(self, conn, command_name, **options):
        """Parses a response from the Redis server"""
        try:
            response = conn.read_response()
        except ResponseError:
            raise
        return response

    def get(self, key: bytes, default: bytes | None) -> bytes | None:
        return self.execute_command("GET", key)
