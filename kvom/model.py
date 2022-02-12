# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic.class_validators import validator
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass
from ulid import ULID
from kvom.database import Database
from kvom.exceptions import PrimaryKeyDuplicateError, PrimaryKeyNotFoundError
from kvom.field import Field, FieldInfo


@dataclass
class PrimaryKey:
    name: str
    field: ModelField


class BaseMeta:
    global_key_prefix: str
    model_key_prefix: str
    database: Database
    primary_key: PrimaryKey
    encoding: str


@dataclass
class DefaultMeta:
    global_key_prefix: Optional[str] = None
    model_key_prefix: Optional[str] = None
    database: Optional[Database] = None
    primary_key: Optional[PrimaryKey] = None
    encoding: Optional[str] = "utf-8"


class BaseModelMeta(ModelMetaclass):
    _meta = BaseMeta

    def __new__(mcs, name, bases, attrs, **kwargs):
        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        meta = attrs.pop("Meta", None)

        base_meta = meta or getattr(cls, "_meta", None)
        meta = meta or getattr(cls, "Meta", None)

        # inherit meta from father class
        if meta and meta != DefaultMeta and meta != base_meta:
            cls._meta = meta
            cls.Meta = meta
        elif base_meta:
            cls._meta = type(
                f"{cls.__name__}Meta", (base_meta,), dict(base_meta.__dict__)
            )
            cls.Meta = cls._meta
            # unset inherited values
            cls._meta.model_key_prefix = None
        else:
            cls._meta = type(
                f"{cls.__name__}Meta",
                (DefaultMeta,),
                dict(DefaultMeta.__dict__),
            )
            cls.Meta = cls._meta

        for field_name, field in cls.__fields__.items():
            if isinstance(field.field_info, FieldInfo):
                # set primary key
                if field.field_info.primary_key:
                    cls._meta.primary_key = PrimaryKey(name=field_name, field=field)

        # get meta attr values from base model if there not set
        if not getattr(cls._meta, "database", None):
            # TODO: get default database connection
            cls._meta.database = getattr(base_meta, "database", None)

        if not getattr(cls._meta, "global_key_prefix", None):
            cls._meta.global_key_prefix = getattr(base_meta, "global_key_prefix", "")

        if not getattr(cls._meta, "model_key_prefix", None):
            cls._meta.model_key_prefix = f"{cls.__module__}.{cls.__name__}"

        if not getattr(cls._meta, "encoding", None):
            cls._meta.encoding = getattr(base_meta, "encoding")

        return cls


class BaseModel(PydanticBaseModel, metaclass=BaseModelMeta):
    pk: Optional[str] = Field(None, primary_key=True)
    Meta = DefaultMeta

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.validate_primary_key()

    @validator("pk", always=True, allow_reuse=True)
    def validate_pk(cls, v):
        return str(ULID) if not v else v

    @classmethod
    def validate_primary_key(cls):
        """Check for a primary key. We need one (and only one)."""
        primary_keys = 0
        for name, field in cls.__fields__.items():
            if getattr(field.field_info, "primary_key", None):
                primary_keys += 1
        if primary_keys == 0:
            raise PrimaryKeyNotFoundError("You must define a primary key for the model")
        elif primary_keys > 1:
            raise PrimaryKeyDuplicateError(
                "You must define only one primary key for a model"
            )

    def key(self):
        """the key for database crud operation"""
        cls = self.__class__
        pk = getattr(cls, cls._meta.primary_key.field.name)
        global_prefix = getattr(cls._meta, "global_key_prefix", "").strip(":")
        model_prefix = getattr(cls._meta, "model_key_prefix", "").strip(":")
        prefix = f"{global_prefix}:{model_prefix}:{pk}"
        return prefix

    @classmethod
    async def get(cls, pk: Any) -> "BaseModel":
        return await cls._meta.database.get(cls, pk)

    async def save(self) -> "BaseModel":
        return await self.__class__._meta.database.save(self)

    async def delete(self):
        return await self.__class__._meta.database.delete(self.key())
