import sqlite3
import atexit
import signal
import sys
from pathlib import Path
from multiprocessing.connection import Connection

from Modules.constants import Status, DB

PASSWORD_DATABASE = Path(__file__).parent.parent / "User_Data/passwords.db"
PASSWORD_DATABASE_SCHEMA = "Passwords(Username TEXT PRIMARY KEY, Password TEXT NOT NULL)"

class QueryObject:
    def __init__(self, request : DB, username: str, data : list[str], pipe : Connection, pid : int):
        self.request = request
        self.username = username
        self.data = data
        self.pipe = pipe
        self.pid = pid
    
    def to_string(self) -> str:
        return f"{self.request} with {self.data} from {self.username} {self.pid}, pipe: {self.pipe}"

class DatabaseManager:
    def __init__(self):
        self.passwords = sqlite3.connect(PASSWORD_DATABASE)
        self.passwords_cursor = self.passwords.cursor()
        self.passwords_cursor.execute(f"CREATE TABLE IF NOT EXISTS {PASSWORD_DATABASE_SCHEMA}")
        self.passwords.commit()

        # Handle kills and interupts by closing
        atexit.register(self.close)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def close(self):
        if hasattr(self, 'passwords') and self.passwords:
            self.passwords.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
    
    def _signal_handler(self, signum, frame):
        self.close()
        sys.exit(0) 

    def insert_user(self, username : str, password : str) -> Status:
        if not username or not password:
            return Status.INVALID_INPUT
        try:
            self.passwords_cursor.execute("INSERT INTO Passwords (Username, Password) VALUES (?, ?)", (username, password))
            self.passwords.commit()
            return Status.SUCCESS
        except sqlite3.IntegrityError:
            return Status.INVALID_INPUT
    
    def delete_user(self, username: str) -> Status:
        if not username:
            return Status.INVALID_INPUT
        self.passwords_cursor.execute("DELETE FROM Passwords WHERE Username = ?", (username,))
        if self.passwords_cursor.rowcount == 0:
            return Status.NOT_FOUND
        self.passwords.commit()
        return Status.SUCCESS
    
    def get_password(self, username : str) -> tuple[Status, str]:
        if not username:
            return (Status.INVALID_INPUT, None)
        self.passwords_cursor.execute("SELECT Password FROM Passwords WHERE Username = ?", (username,))
        result = self.passwords_cursor.fetchone()
        return (Status.SUCCESS, result[0]) if result else (Status.NOT_FOUND, None)
    
    def handler(self, request : QueryObject) -> tuple[Status, str]:
        match request.request:
            case DB.CHECK_USERNAME:
                status, true_password = self.get_password(request.data[0])
                if status == Status.SUCCESS:
                    return (Status.SUCCESS, request.data[0])
                return (status, None)
            case DB.CHECK_PASSWORD:
                username, password = request.data[0], request.data[1]
                status, true_password = self.get_password(username)
                if status == Status.SUCCESS:
                    return (Status.SUCCESS, username) if password == true_password else (Status.FAIL, username)
                return (status, None)
            case DB.ADD_USER:
                username, password = request.data[0], request.data[1]
                status, _password = self.get_password(username)
                if status == Status.SUCCESS:
                    return(Status.DUPLICATE, None)
                status = self.insert_user(request.data[0], request.data[1])
                return (status, None)
            case _:
                return (Status.INVALID_INPUT, None)
    
    def empty_table(self) -> Status:
        try:
            self.passwords_cursor.execute("DELETE FROM Passwords")
            self.passwords.commit()
            return Status.SUCCESS
        except sqlite3.Error:
            return Status.ERROR
    
    def output(self) -> list[list[str]] | Status:
        try:
            self.passwords_cursor.execute("SELECT * FROM Passwords")
        except sqlite3.OperationalError:
            return Status.ERROR
        rows = self.passwords_cursor.fetchall()
        return rows if rows else Status.NOT_FOUND

