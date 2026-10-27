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


def generate_flag() -> str:
    alphabet: str = string.ascii_uppercase + string.digits

    return "".join(random.choices(alphabet, k=31)) + "="
