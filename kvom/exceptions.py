# -*- coding: utf-8 -*-


class KVOMError(Exception):
    pass


class PrimaryKeyNotFoundError(KVOMError):
    pass


class PrimaryKeyDuplicateError(KVOMError):
    pass
