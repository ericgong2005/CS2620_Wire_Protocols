from Modules.constants import Status, DB

class QueryObject:
    def __init__(self, request : DB = DB.EMPTY, username: str = None, pid : int = None, data : list[str] = [""]):
        self.request = request if request else DB.EMPTY
        self.username = username
        self.pid = pid
        self.data = data if data else [""]

    def serialize(self) -> bytes:
        if self.data == []:
            self.data = [""]
        return (
            f"{self.request.name}\n"
            f"{self.username if self.username else ""}\n"
            f"{self.pid if self.pid else ""}\n"
            f"{len(self.data)}\n"
            f"{'\n'.join(self.data)}\n"
        ).encode("utf-8")
    
    def deserialize(self, serial : bytes) -> tuple[Status, bytes]:
        dserial = serial.decode("utf-8")
        lines = dserial.splitlines()
        try:
            if len(lines) < 4:
                return (Status.INCOMPLETE, serial)

            # Parse the expected fields.
            request = DB[lines[0]]
            username = lines[1]
            pid = int(lines[2]) if lines[2] else None
            data_len = int(lines[3])

            # Ensure there are enough lines for all data items.
            if len(lines) < 4 + data_len:
                return (Status.INCOMPLETE, serial)

            data = lines[4:4 + data_len]

            self.request = request
            self.username = username
            self.pid = pid
            self.data = data

            current = lines[0 : 4 + data_len]
            drop = '\n'.join(current) + "\n"
            dserial = dserial[len(drop):]
            return (Status.SUCCESS, dserial.encode("utf-8"))
        except Exception:
            return (Status.FAIL, serial)

    def to_string(self) -> str:
        return f"{self.request} with {self.data} from {self.username} {self.pid}"
    
class ResponseObject:
    def __init__(self, request : DB = DB.EMPTY, status : Status = Status.FAIL, data : list[str] = [""]):
        self.request = request if request else DB.EMPTY
        self.status = status if status else Status.FAIL
        self.data = data if data else [""]

    def update(self, request : DB = DB.EMPTY, status : Status = Status.FAIL, data : list[str] = []):
        self.request = request if request else DB.EMPTY
        self.status = status if status else Status.FAIL
        self.data = data if data else [""]
    
    def serialize(self) -> bytes:
        if self.data == []:
            self.data = [""]
        return (
            f"{self.request.name}\n"
            f"{self.status.name}\n"
            f"{len(self.data)}\n"
            f"{'\n'.join(self.data)}\n"
        ).encode("utf-8")
    
    def deserialize(self, serial : str) -> tuple[Status, bytes]:
        dserial = serial.decode("utf-8")
        lines = dserial.splitlines()
        try:
            if len(lines) < 3:
                return (Status.INCOMPLETE, serial)

            # Parse the expected fields.
            request = DB[lines[0]]
            status = Status[lines[1]]
            data_len = int(lines[2])
            if data_len == 0:
                data_len = data_len + 1

            # Ensure there are enough lines for all data items.
            if len(lines) < 3 + data_len:
                return (Status.INCOMPLETE, serial)

            data = lines[3:3 + data_len]

            self.request = request
            self.status = status
            self.data = data

            current = lines[0 : 3 + data_len]
            drop = '\n'.join(current) + "\n"
            dserial = dserial[len(drop):]
            return (Status.SUCCESS, dserial.encode("utf-8"))
        except Exception:
            return (Status.FAIL, serial)

    def to_string(self) -> str:
        return f"{self.request} returns {self.status} with {self.data}"
