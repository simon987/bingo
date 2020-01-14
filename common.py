import logging
import sys
from logging import FileHandler, StreamHandler

from models import DB

config = {
    "API_PORT": 3000,
    "API_HOST": "0.0.0.0",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": 6379,
    "FLASK_SECRET": "secret!",
    "VERBOSE": False,
}

logger = logging.getLogger("default")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
file_handler = FileHandler("bingo.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(StreamHandler(sys.stdout))

db = DB()
