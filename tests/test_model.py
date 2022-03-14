# -*- coding: utf-8 -*-
import pytest

from kvom.exceptions import NoSourceError
from kvom.field import Field
from kvom.model import BaseModel
from kvom.source import Source


class Movie(BaseModel):
    class Meta:
        source = Source("redis://localhost:6379/0")
        prefix = "movie"
        encoding = "utf-8"

    title: str
    year: int
    director: str


def test_model_meta_default():
    class User(BaseModel):
        name: str
        age: int

        class Meta:
            source = Source("redis://localhost:6379/0")

    assert User.Meta.prefix == "tests.test_model:user"
    assert User.Meta.encoding == "utf-8"
    assert not User.Meta.embedded
    assert User.Meta.primary_key == "pk"

    user = User(name="John Doe", age=42)
    assert user.key == "tests.test_model:user:pk"


def test_model_meta_custom():
    class User(BaseModel):
        class Meta:
            source = Source("redis://localhost:6379/0")
            embedded = True
            encoding = "utf-16"
            primary_key = "name"
            prefix = "custom_prefix"

        name: str = Field(default="chaojie")
        age: int

    assert User.Meta.prefix == "custom_prefix"
    assert User.Meta.encoding == "utf-16"
    assert User.Meta.embedded
    assert User.Meta.primary_key == "name"

    user = User(name="test", age=10)
    assert user.key == "user:name"


def test_model_meta_inherited():
    class User(BaseModel):
        class Meta:
            source = Source("redis://localhost:6379/0")
            prefix = "test"
            encoding = "utf-8"

        name: str
        age: int

    class Admin(User):
        pass

    assert Admin.Meta.prefix == "test"
    assert Admin.Meta.encoding == "utf-8"


def test_model_key_model_key_prefix():
    movie = Movie(title="The Matrix", year=1999, director="Lana Wachowski")
    assert movie.key == "movie:pk"


def test_model_meta_source():
    class User(BaseModel):
        name: str

    with pytest.raises(NoSourceError):
        User(name="test")


def test_model_base():
    movie = Movie(title="Harry Potter", year=2001, director="Chris Columbus")
    movie.save()
    movie_db = Movie.get(movie.key)
    assert movie_db.title == "Harry Potter"
    assert movie_db.year == 2001
    assert movie_db.director == "Chris Columbus"
    movie.delete()
    assert not Movie.get(movie.key)
