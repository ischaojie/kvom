# -*- coding: utf-8 -*-
from kvom.database import Database


def test_database_init():
    db = Database("redis://localhost:6379/0")
    db.set()
