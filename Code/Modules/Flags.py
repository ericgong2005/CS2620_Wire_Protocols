'''
This file contains the flags used by the DataObject class
'''
from enum import Enum

class Request(Enum):
    EMPTY = 0
    CHECK_USERNAME = 1
    CHECK_PASSWORD = 2
    CREATE_USER = 3
    CONFIRM_LOGIN = 4
    CONFIRM_LOGOUT = 5
    GET_ONLINE_USERS = 6
    GET_USERS = 7
    SEND_MESSAGE = 8
    ALERT_MESSAGE = 9
    GET_MESSAGE = 10
    CONFIRM_READ = 11
    DELETE_MESSAGE = 12
    DELETE_USER = 13

class Status(Enum):
    PENDING = 0
    SUCCESS = 1
    MATCH = 2
    NO_MATCH = 3
    ERROR = 4

class EncodeType(Enum):
    CUSTOM = 0
    JSON = 1