from enum import Enum

class Status(Enum):
    ERROR = -1
    SUCCESS = 0
    FAIL = 1
    INCOMPLETE = 2
    INVALID_INPUT = 3
    NOT_FOUND = 4
    DUPLICATE = 5
    ALERT = 6

class DB(Enum):
    EMPTY = -1
    CHECK_USERNAME = 0
    CHECK_PASSWORD = 1
    ADD_USER = 2
    LOGIN = 3
    LOGOUT = 4
    CURRENT_USERS = 5
    NOTIFY = 6
