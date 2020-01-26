import logging
import sys
import os
from logging import FileHandler, StreamHandler

from models import DB

config = {
    "API_PORT": int(os.environ.get("BINGO_API_PORT", "3000")),
    "API_HOST": os.environ.get("BINGO_API_HOST", "0.0.0.0"),
    "REDIS_HOST": os.environ.get("BINGO_REDIS_HOST", "localhost"),
    "REDIS_PORT": int(os.environ.get("BINGO_REDIS_PORT", "6379")),
    "FLASK_SECRET": os.environ.get("BINGO_FLASK_SECRET", "secret!"),
    "VERBOSE": bool(os.environ.get("BINGO_VERBOSE", "True")),
}

logger = logging.getLogger("default")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
file_handler = FileHandler("bingo.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(StreamHandler(sys.stdout))

db = DB()
