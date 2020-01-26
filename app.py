import logging

from flask import Flask, request, send_file, session
from flask_socketio import Namespace, SocketIO, emit, join_room

from common import config, db
from models import BingoGame, GameState, GameMode, User
from util import is_valid_id

ERR_INVALID_ID = "Invalid identifier"
ERR_BAD_REQUEST = "Bad request"

app = Flask(__name__)
app.config['SECRET_KEY'] = config["FLASK_SECRET"]

socketio = SocketIO(app, async_mode="eventlet")

logger = logging.getLogger("default")


@app.route("/")
def page_index():
    return send_file("web/index.html")


@app.route("/<room>")
def play(room):
    return send_file("web/room.html")


def log(message, contents, room=None):
    if config["VERBOSE"]:
        logger.info("<%s|%s> [%s] %s:%s" % (
            request.remote_addr, request.user_agent, room if room else "~", message, str(contents)))
    else:
        logger.info("[%s] %s:%s" % (room if room else "~", message, str(contents)))


class BingoNamespace(Namespace):
    def __init__(self):
        super().__init__("/socket")

    def on_get_end_message(self, message):
        room = message["room"] if "room" in message else None
        log("get_end_message", message, room=room)

        if room is None or "oid" not in message:
            emit("create_game_rsp", {
                "error": ERR_BAD_REQUEST
            })
            return

        game = db.get_game(room)
        if game.admin == message["oid"]:
            emit("end_message", {
                "text": "Game has ended, replay?",
                "replay": True,
            })
        else:
            emit("end_message", {
                "text": "Waiting for %s to restart game..." % (db.get_user(game.admin).name, ),
                "replay": False,
            })

    def on_cell_click(self, message):
        room = message["room"]
        log("cell_click", message, room)

        user = db.get_user(message["oid"])
        card = db.get_card(message["card"])
        cell = card.cells[message["cidx"]]
        game = db.get_game(room)

        # if game.mode == GameMode.FREE or game.mode:

        if not cell.checked or card.last_cell == message["cidx"]:
            card.check_cell(message["cidx"])
            card.last_cell = message["cidx"]
            db.save_card(card)

            emit("card_state", {"card": card.serialize()}, room=room)

            if card.moves_until_win() == 0:
                game = db.get_game(room)
                game.winners.append(user.oid)

                if game.should_end():
                    game.state = GameState.ENDED
                    emit("game_state", {"state": game.state.name}, room=room)
                db.save_game(game)

    def on_get_card(self, message):
        room = message["room"]
        log("get_card", message, room)

        user = db.get_user(message["oid"])
        game = db.get_game(room)

        if room in user.cards:
            card = db.get_card(user.cards[room])
        else:
            card = game.generate_card()
            user.cards[room] = card.oid
            db.save_card(card)
            db.save_user(user)

        emit("get_card_rsp", {
            "card": card.serialize(),
            "parent": user.name
        })

        emit("card_state", {
            "card": card.serialize(),
            "parent": user.name
        }, room=room)

        for player in game.players:
            if player != user.oid:
                other_user = db.get_user(player)
                if room in other_user.cards:
                    other_card = db.get_card(other_user.cards[room])
                    emit("card_state", {"card": other_card.serialize(), "parent": other_user.name})

    def on_create_game(self, message):
        room = message["room"] if "room" in message else None
        log("create_game", message, room)

        if "oid" not in message or room is None or "mode" not in message or "pool" not in message:
            emit("create_game_rsp", {
                "created": False,
                "error": ERR_BAD_REQUEST
            })
            return

        if not is_valid_id(room):
            emit("create_game_rsp", {
                "created": False,
                "error": ERR_INVALID_ID
            })
            return

        game = db.get_game(room)
        if game.state is GameState.CREATING or (game.state is GameState.ENDED and game.admin == message["oid"]):
            for oid in game.players:
                player = db.get_user(oid)
                if room in player.cards:
                    del player.cards[room]
                    db.save_user(player)

            game.state = GameState.PLAYING
            game.mode = GameMode[message["mode"]]
            game.pool = message["pool"]
            game.admin = message["oid"]
            db.save_game(game)

            emit("game_state", {"state": game.state.name, }, room=room)
            emit("style_state", {"style": game.style}, room=room)
            emit("create_game_rsp", {
                "created": True,
            })

    def on_join(self, message):
        log("join", message)

        room = message["room"]
        name = message["name"]

        if not is_valid_id(room) or not is_valid_id(name):
            emit("join_rsp", {
                "error": ERR_INVALID_ID
            }, room=room)
            return

        user = None
        if "oid" in message:
            user = db.get_user(message["oid"])
            if not user:
                emit("join_rsp", {
                    "ok": False
                })
                return

        if not user:
            user = User(name=name)
            db.save_user(user)
        session["user"] = user.oid

        game = db.get_game(message["room"])
        if not game:
            game = BingoGame(room, user.oid)
        emit("style_state", {
            "style": game.style
        })

        join_room(room)
        game.players.add(user.oid)
        db.save_game(game)

        emit("join_rsp", {
            "ok": True,
            "state": game.state.name,
            "oid": user.oid
        })

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass


socketio.on_namespace(BingoNamespace())
db.flush()

if __name__ == "__main__":
    socketio.run(
        app=app,
        port=config["API_PORT"],
        host=config["API_HOST"],
    )
