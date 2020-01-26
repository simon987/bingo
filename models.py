from enum import Enum
from uuid import uuid4
import random
import math

import redis
import json
import common


class BingoCell:

    def __init__(self, text, checked=False, free=False, shake=False):
        self.text = text
        self.free = free
        self.checked = checked
        self.shake = shake

    def serialize(self):
        return self.__dict__

    def __repr__(self):
        return self.text

    @staticmethod
    def deserialize(j):
        return BingoCell(
            text=j["text"],
            free=bool(j["free"]),
            checked=bool(j["checked"]),
            shake=bool(j["shake"])
        )


class BingoCard:
    def __init__(self, size, cells=None, oid=None, last_cell=None):
        if cells is None:
            cells = []
        self.cells = cells
        if oid is None:
            oid = uuid4().hex
        self.oid = oid
        self.size = size
        self.last_cell = last_cell

    def serialize(self):
        return {
            "oid": self.oid,
            "cells": tuple(c.serialize() for c in self.cells),
            "size": self.size,
            "last_cell": self.last_cell,
            "moves_until_win": self.moves_until_win(),
        }

    def moves_until_win(self):
        return min(sum(1 for c in line if not c.checked) for line in self._lines())

    def _lines(self):
        return [
            *(self._row(row) for row in range(0, self.size)),
            *(self._col(col) for col in range(0, self.size)),
            self._diag_left(),
            self._diag_right(),
        ]

    def check_cell(self, cell_idx):
        cell = self.cells[cell_idx]
        cell.checked = not cell.checked
        self._update_shaking(cell)

    def _update_shaking(self, cell):
        for c in self.cells:
            c.shake = False
        if cell.checked:
            for line in self._lines():
                moves_remaining = sum(1 for c in line if not c.checked)
                if cell in line and moves_remaining <= self.size / 2 and moves_remaining <= 3:
                    for c in line:
                        c.shake = not c.checked

    def _row(self, idx):
        return self.cells[idx * self.size:idx * self.size + self.size]

    def _col(self, idx):
        return [self.cells[c] for c in range(0, len(self.cells)) if c % self.size == idx]

    def _diag_left(self):
        return [self.cells[c] for c in range(0, len(self.cells), self.size + 1)]

    def _diag_right(self):
        return [self.cells[c] for c in range(self.size - 1, len(self.cells) - 1, self.size - 1)]

    @staticmethod
    def deserialize(j):
        return BingoCard(
            cells=tuple(BingoCell.deserialize(c) for c in j["cells"]),
            size=j["size"],
            oid=j["oid"],
            last_cell=j["last_cell"]
        )


class GameMode(Enum):
    FREE = "free"
    ADMIN = "admin"
    CPU = "cpu"


class GameState(Enum):
    CREATING = "creating"
    PLAYING = "playing"
    ENDED = "ended"


class BingoGame:
    _default_style = {
        "cell": {
            "base": 0xBD93F9,
            "checked": 0xFF5555,
            "hover": 0xFF79C6,
            "text": 0x111111
        },
        "card": {
            "base": 0xFF5555,
            "text": 0x50FA7B
        },
        "background": 0x282A36,
        "message": 0xF8F8F2,
        "font": "Hack, 'Roboto Mono', 'Lucida Console'"
    }

    def __init__(self, room, admin, mode=GameMode.FREE, pool=None, state=GameState.CREATING,
                 players=None, winners=None, style=None, valid_cells=None):
        self.room = room
        self.mode = mode
        self.admin = admin
        if pool is None:
            pool = []
        self.pool = pool
        self.state = state
        if players is None:
            players = set()
        self.players = players
        if winners is None:
            winners = []
        self.winners = winners
        if style is None:
            style = BingoGame._default_style
        self.style = style
        if valid_cells is None:
            valid_cells = []
        self.valid_cells = valid_cells

    def should_end(self):
        # TODO: add winner count
        return len(self.winners) > 0

    def generate_card(self):
        # TODO: customizable maximum size
        size = math.floor(math.sqrt(len(self.pool)))
        items = random.sample(self.pool, k=size * size)
        return BingoCard(size, cells=[BingoCell(x) for x in items])

    def serialize(self):
        return {
            "room": self.room,
            "mode": self.mode.name,
            "admin": self.admin,
            "state": self.state.name,
            "pool": self.pool,
            "players": list(self.players),
            "winners": self.winners,
            "style": self.style,
            "valid_cells": self.valid_cells,
        }

    @staticmethod
    def deserialize(j):
        return BingoGame(
            room=j["room"],
            mode=GameMode[j["mode"]],
            pool=j["pool"],
            admin=j["admin"],
            state=GameState[j["state"]],
            players=set(j["players"]),
            winners=j["winners"],
            style=j["style"],
            valid_cells=j["valid_cells"],
        )


class User:
    def __init__(self, name, oid=None, cards=None):
        if cards is None:
            cards = {}
        if oid is None:
            oid = uuid4().hex
        self.name = name
        self.oid = oid
        self.cards = cards

    @staticmethod
    def deserialize(j):
        return User(
            name=j["name"],
            oid=j["oid"],
            cards=j["cards"],
        )

    def serialize(self):
        return self.__dict__


class DB:
    _prefix = "bingo:"

    def __init__(self):
        self._rdb = redis.Redis(
            host=common.config["REDIS_HOST"],
            port=common.config["REDIS_PORT"]
        )

    def flush(self):
        keys = self._rdb.keys(DB._prefix + "*")
        if keys:
            self._rdb.delete(*keys)

    def _get(self, name):
        text = self._rdb.get(DB._prefix + name)
        # print("<GET> %s = %s" % (name, text))
        if text:
            return json.loads(text)

    def _set(self, name, value):
        self._rdb.set(DB._prefix + name, json.dumps(value, separators=(",", ":")))
        # print("<SET> %s -> %s" % (name, value))
        # self._rdb.expire(DB._prefix + name, 3600 * 24 * 14)

    def get_card(self, oid):
        j = self._get(oid)
        if j:
            return BingoCard.deserialize(j)

    def save_card(self, card):
        self._set(card.oid, card.serialize())

    def get_game(self, room):
        j = self._get("game:" + room)
        if j:
            return BingoGame.deserialize(j)

    def save_game(self, game: BingoGame):
        self._set("game:" + game.room, game.serialize())

    def get_user(self, oid):
        j = self._get(oid)
        if j:
            return User.deserialize(j)

    def save_user(self, user):
        self._set(user.oid, user.serialize())
