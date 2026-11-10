import logging
import pathlib
import random
import string
import typing
from enum import Enum

IS_COLOR_ENABLED = False
IS_LOGGER_CREATED = False


class Status(Enum):
    OK = 101
    DOWN = 104
    CHECKER_DISABLED = 109
    ERROR = 110
    NOT_YET_CHECKED = 124


class Action(Enum):
    CHECK_SLA = "CHECK_SLA"
    PUT_FLAG = "PUT_FLAG"
    GET_FLAG = "GET_FLAG"


# From https://stackoverflow.com/questions/1181919/python-base-36-encoding and modified
def base36encode(number: int) -> str:
    """Converts an integer to a base36 string."""

    alphabet = string.digits + string.ascii_uppercase

    base36 = ""

    if 0 <= number < len(alphabet):
        return alphabet[number].zfill(2)

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return base36


def generate_flag(team: int, nround: int, nservice: int = 0) -> str:
    alphabet: str = string.ascii_uppercase + string.digits

    return (
        base36encode(nround)
        + base36encode(team)
        + base36encode(nservice)
        + "".join(random.choices(alphabet, k=25))
        + "="
    )


def get_logger(module: str) -> logging.Logger:
    logger_path = pathlib.Path("app.log")

    global IS_LOGGER_CREATED

    if not IS_LOGGER_CREATED and logger_path.exists():
        logger_path.unlink()
        IS_LOGGER_CREATED = True

    logger = logging.getLogger(module)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("app.log", mode="a", encoding="utf-8")

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    formatter = CustomFormatter()
    file_formatter = logging.Formatter(
        "{asctime} - {levelname} - {name} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(file_formatter)

    return logger


class CustomFormatter(logging.Formatter):
    grey: str = "\x1b[38;20m"
    green: str = "\x1b[32;20m"
    yellow: str = "\x1b[33;20m"
    red: str = "\x1b[31;20m"
    bold_red: str = "\x1b[31;1m"
    reset: str = "\x1b[0m"
    format: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    FORMATS: typing.ClassVar = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
        "No_Color": format,
    }

    def format(self, record):
        if IS_COLOR_ENABLED:
            log_fmt = self.FORMATS.get(record.levelno)
        else:
            log_fmt = self.FORMATS.get("No_Color")
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
