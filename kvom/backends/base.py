from __future__ import annotations


class ClientBackend:
    def conn(self) -> None:
        raise NotImplementedError()

    def disconn(self) -> None:
        raise NotImplementedError()

    def conn_pool(self) -> ConnPoolBackend:
        raise NotImplementedError()


class ConnPoolBackend:
    def acquire(self) -> None:
        raise NotImplementedError()

    def release(self) -> None:
        raise NotImplementedError()

    def get(self, key: bytes, default: bytes | None = None) -> bytes | None:
        raise NotImplementedError()

    def set(self, key: bytes, value: bytes) -> bool:
        raise NotImplementedError

    def delete(self, key: bytes) -> bool:
        raise NotImplementedError
