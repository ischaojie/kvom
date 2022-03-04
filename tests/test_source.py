# -*- coding: utf-8 -*-
import pytest

from kvom.source import RedisBackend, Source, SourceURL


@pytest.mark.parametrize(
    "url, dialect",
    [
        ("redis://localhost:6379/0", "redis"),
        ("mongodb://localhost:27017/", "mongodb"),
        ("memcached://localhost:11211/", "memcached"),
    ],
)
def test_source_url(url, dialect):
    url = SourceURL(url)
    assert url.dialect == dialect


def test_redis_backend():
    backend = RedisBackend("redis://localhost:6379/0")
    assert backend.set("ping", "pong")
    assert backend.get("ping") == "pong"
    assert backend.delete("ping")


# def test_mongo_backend():
#     backend = MongoBackend("mongodb://localhost:27017/test")
#     assert backend.set("ping", "pong")
#     assert backend.get("ping") == "pong"
#     assert backend.delete("ping")
#     assert backend._document_name == "kvom"


# def test_mongo_backend_custom_document():
#     backend = MongoBackend("mongodb://localhost:27017/test", document="test-kvom")
#     assert backend.set("ping", "{'a': 'b'}")
#     assert backend.get("ping") == "{'a': 'b'}"
#     assert backend.delete("ping")


@pytest.mark.parametrize(
    "url",
    [
        "redis://localhost:6379/0",
    ],
)
def test_source(url):
    source = Source(url)
    assert source.set("ping", "pong")
    assert source.get("ping") == "pong"
    assert source.set("ping", "pong2")
    assert source.get("ping") == "pong2"
    assert source.delete("ping")
    assert source.get("ping") is None
