from uuid import uuid4

import redis
import json
from common import config


class BingoCell:

    def __init__(self, text, checked=False, free=False):
        self.text = text
        self.free = free
        self.checked = checked

    def serialize(self):
        return self.__dict__

    @staticmethod
    def deserialize(j):
        return BingoCell(
            text=j["text"],
            free=bool(j["free"]),
            checked=bool(j["checked"])
        )


class Row:


class BingoCard:
    def __init__(self, size, cells=None, oid=None):
        if cells is None:
            self.cells = []
        else:
            self.cells = cells
        if oid is None:
            self.oid = uuid4().hex
        else:
            self.oid = oid
        self.size = size

    def serialize(self):
        return {
            "oid": self.oid,
            "cells": [c.serialize() for c in self.cells]
        }

    def __getitem__(self, col):


    @staticmethod
    def deserialize(text):
        j = json.loads(text)
        return BingoCard(cells=[
            BingoCell.deserialize(c) for c in j["cells"]
        ])


class DB:

    _prefix = "bingo:"

    def __init__(self):
        self._rdb = redis.Redis(
            host=config["REDIS_HOST"],
            port=config["REDIS_PORT"]
        )

    def flush(self):
        self._rdb.delete(self._rdb.keys(DB._prefix + "*"))

    def _get(self, name):
        return self._rdb.get(DB._prefix + name)

    def _set(self, name, value):
        return self._rdb.set(DB._prefix + name, value)

    def get_card(self, oid):
        return BingoCard.deserialize(self._get(oid))

    def save_card(self, card):
        self._set(card.oid, card.serialize())


c = BingoCard(
    size=4,
    cells=[
    BingoCell("test")
])
print(c.serialize())
