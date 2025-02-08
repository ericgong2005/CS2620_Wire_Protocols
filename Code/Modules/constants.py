from enum import Enum

class Status(Enum):
    ERROR = -1
    SUCCESS = 0
    INVALID_INPUT = 1
    NOT_FOUND = 2