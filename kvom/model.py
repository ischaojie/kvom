# -*- coding: utf-8 -*-
import secrets
from typing import Any, ClassVar, Optional, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import validator
from pydantic.main import ModelMetaclass

from kvom.exceptions import NoSourceError, PrimaryKeyDuplicated, PrimaryKeyNotFound
from kvom.field import Field, FieldInfo
from kvom.source import Source
from kvom.field import Field

__all__ = ["BaseModel"]

T = TypeVar("T", bound="BaseModel")


class BaseMeta:
    # data source
    source: Optional[Source] = None

    # the model encoding format when saving to the store
    encoding: str = "utf-8"

    prefix: Optional[str] = None

    primary_key: Optional[str] = None

    # is support embedded model
    embedded: bool = False


def _set_meta_default(cls, meta, base_meta):
    if not getattr(meta, "encoding", None):
        meta.encoding = getattr(base_meta, "encoding", "utf-8")

    if not getattr(meta, "prefix", None):
        meta.prefix = f"{cls.__module__}:{cls.__name__}".lower()

    if not getattr(meta, "embedded", None):
        meta.embedded = getattr(base_meta, "embedded", False)

    if not getattr(meta, "source", None):
        meta.source = getattr(base_meta, "source", None)


class BaseModelMeta(ModelMetaclass):
    _meta: BaseMeta

    def __new__(mcs, name, bases, attrs, **kwargs):
        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        meta = attrs.get("Meta", None)

        # if cls not defined Meta, get from parent
        meta = meta or getattr(cls, "Meta", None)
        base_meta = getattr(cls, "_meta", None)
        # no inherited, defined Meta
        if meta and meta != BaseMeta and meta != base_meta:
            cls.Meta = meta
            cls._meta = meta
        # inherited Meta
        elif base_meta:
            cls._meta = type(
                f"{cls.__name__}Meta", (base_meta,), dict(base_meta.__dict__)
            )
            cls.Meta = cls._meta
        # no defined Meta, no inherited, use default
        else:
            cls._meta = type(
                f"{cls.__name__}Meta", (BaseMeta,), dict(BaseMeta.__dict__)
            )
            cls.Meta = cls._meta

        for f_name, field in cls.__fields__.items():
            if isinstance(field.field_info, FieldInfo):
                cls._meta.primary_key = f_name

        # set Meta default value if there is no defined
        _set_meta_default(cls, cls._meta, base_meta)

        return cls


class BaseModel(PydanticBaseModel, metaclass=BaseModelMeta):
    """
    Example:

    class UserModel(BaseModel):
        class Meta:
            can_edit = False

        name: str
        age: int

    user = UserModel(name="John", age=18)
    user.save()

    """
    pk: Optional[str] = Field(default=None, primary_key=True)

    pk: Optional[str] = Field(default=None, primary_key=True)

    Meta = BaseMeta
    identity: ClassVar[str]

    def __init__(__pydantic_self__, **data: Any) -> None:
        super().__init__(**data)
        __pydantic_self__.validate_source()
        __pydantic_self__.validate_pk()

    @property
    def key(self):
        prefix = getattr(self._meta, "prefix", "")
        primary_key = getattr(self._meta, "primary_key")
        return f"{prefix}:{primary_key}".strip(":")

    @classmethod
    def validate_source(cls):
        if cls._meta.source is None or not isinstance(cls._meta.source, Source):
            raise NoSourceError("Model must have a Source client")

    @classmethod
    def validate_pk(cls):
        primary_keys = 0
        for name, field in cls.__fields__.items():
            if getattr(field.field_info, "primary_key", None):
                primary_keys += 1
        if primary_keys == 0:
            raise PrimaryKeyNotFound("You must define a primary key for the model")
        elif primary_keys > 1:
            raise PrimaryKeyDuplicated(
                "You must define only one primary key for a model"
            )

    @validator("pk", always=True, allow_reuse=True)
    def pk_or_default(cls, v):
        if not v:
            v = secrets.token_hex(4)
        return v

    @classmethod
    def get(cls, key: str) -> Optional["BaseModel"]:
        data = cls._meta.source.get(key)
        if not data:
            return None
        return cls.parse_raw(data, encoding=cls._meta.encoding)

    def save(self) -> bool:
        cls = self.__class__
        return cls._meta.source.set(self.key, self.json())

    def delete(self) -> bool:
        cls = self.__class__
        return cls._meta.source.delete(self.key)
