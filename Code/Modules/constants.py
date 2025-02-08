from enum import Enum

class Status(Enum):
    ERROR = -1
    SUCCESS = 0
    FAIL = 1
    INVALID_INPUT = 2
    NOT_FOUND = 3

class DB(Enum):
    CHECK_USERNAME = 0
    CHECK_PASSWORD = 1
    ADD_USER = 2
