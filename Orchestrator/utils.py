import logging
import os
import random
import string
from enum import Enum


class Status(Enum):
    OK = 101
    DOWN = 104
    CHECKER_DISABLED = 109
    ERROR = 110


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
    # TODO: Figure out how to assign service numbers

    alphabet: str = string.ascii_uppercase + string.digits

    return (
        base36encode(nround)
        + base36encode(team)
        + base36encode(nservice)
        + "".join(random.choices(alphabet, k=25))
        + "="
    )


def get_logger(module: str) -> logging.Logger:

    os.remove("app.log")

    logger = logging.getLogger(module)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("app.log", mode="a", encoding="utf-8")

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    formatter = logging.Formatter(
        "{asctime} - {levelname} - {name} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    return logger
