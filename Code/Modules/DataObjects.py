'''
This file is contains the DataObject and MessageObject Classes which are used to 
serialize and pass data between the client and server processes, as well as between
server processes
'''

from typing import Literal
import time
import json

from Modules.Flags import Request, Status, EncodeType
from Modules.Constants import ENCODE_TYPE, CURRENT_VERSION

# Encoding and Decoding functions for Custom Wire Protocol, details in documentation
def byte_encode(input : bytes) -> bytes:
    '''
    Encode the string by replacing b"\n" with b"%1" and b"%" with b"%0"
    '''
    encoded = bytearray()  
    for byte in input:
        if byte == ord("\n"):
            encoded.extend(b"%1")
        elif byte == ord("%"):
            encoded.extend(b"%0")
        else:
            encoded.append(byte)
    return bytes(encoded)

def byte_decode(input : bytes) -> bytes:
    '''
    Encode the bytestring by replacing b"%1" with b"\n" and b"%0" with b"%" 
    '''
    special = False
    decoded = bytearray()
    for byte in input:
        if byte == ord("\n"):
            raise Exception(r"Invalid Encoding: contains \n")
        elif special:
            special = False
            if byte == ord("1"):
                decoded.extend(b"\n")
            elif byte == ord("0"):
                decoded.extend(b"%")
            else:
                raise Exception(r"Invalid Encoding: % not followed by 0 or 1")
        elif byte == ord("%"):
            special = True
        else:
            decoded.append(byte)
    if special:
        raise Exception(r"Invalid Encoding: % at the end")
    return bytes(decoded)


# Dataobject for Client-Server communication and inter-process communication within the server
class DataObject:
    def __init__(self, 
                 method : Literal["args", "serial"] = "args", 
                 serial : bytes = b"", 
                 request : Request = Request.EMPTY, 
                 status : Status = Status.PENDING, 
                 sequence : int = 0,
                 user: str = "",
                 datalen: int = 0,
                 data: list[str] = []):
        self.encode_type = ENCODE_TYPE
        self.version = CURRENT_VERSION
        if method == "serial":
            self.deserialize(serial)
            self.typecheck()
        elif method == "args":
            # Have 0 be the indicator for assigning a sequence number by the time of the current system
            sequence = int(time.time()) if sequence == 0 else sequence
            self.request = request
            self.status = status
            self.sequence = sequence
            self.user = user
            self.datalen = datalen
            self.data = data
            self.typecheck()
        else:
            raise Exception("Invalid DataObject Instantiation Method")
    
    def typecheck(self):
        '''
        Checks typing and basic assertions for each property
        '''
        if not self.encode_type or not isinstance(self.encode_type, EncodeType):
            raise Exception("Invalid DataObject encoding method Detected")
        if not self.version or not isinstance(self.version, str):
            raise Exception("Invalid DataObject version Detected")
        if not self.request or not isinstance(self.request, Request):
            raise Exception("Invalid DataObject request Detected")
        if not self.status or not isinstance(self.status, Status):
            raise Exception("Invalid DataObject status Detected")
        if self.sequence == None or not isinstance(self.sequence, int):
            raise Exception("Invalid DataObject sequence Detected")
        if self.user == None or not isinstance(self.user, str):
            raise Exception("Invalid DataObject user Detected")
        if (self.datalen == None or not isinstance(self.datalen, int) or self.data == None
            or not isinstance(self.data, list) or self.datalen != len(self.data)):
            raise Exception("Invalid DataObject datalen and data Detected")
    
    def update(self, 
                 method : Literal["args", "serial"] = "args", 
                 serial : bytes = b"", 
                 request : Request = None, 
                 status : Status = None, 
                 sequence : int = None,
                 user: str = None,
                 datalen: int = None,
                 data: list[str] = None):
        if method == "serial":
            self.deserialize(serial)
            self.typecheck()
        elif method == "args":
            self.request = request if request != None else self.request
            self.status = status if status != None else self.status
            self.sequence = sequence if sequence != None else self.sequence
            self.user = user if user != None else self.user
            self.datalen = datalen if datalen != None else self.datalen
            self.data = data if data != None else self.data
            self.typecheck()
        else:
            raise Exception("Invalid DataObject Update Method")

    def serialize(self):
        '''
        Serialize the object first removing "\n" from each field via encode, 
        joining feilds with "\n", removing "\n" once again via encode,
        then surrounding the entire bytestring with "\n"
        '''
        self.typecheck()
        if self.encode_type == EncodeType.CUSTOM:
            serial_list = [
                self.version.encode("utf-8"),
                str(self.request.value).encode("utf-8"),
                str(self.status.value).encode("utf-8"),
                str(self.sequence).encode("utf-8"),
                self.user.encode("utf-8"),
                str(self.datalen).encode("utf-8")
            ]

            serial_data = bytearray()  
            if self.datalen != 0:
                serial_data.extend(byte_encode(self.data[0].encode("utf-8")))
                for entry in self.data[1:]:
                    serial_data.extend(b"\n")
                    serial_data.extend(byte_encode(entry.encode("utf-8")))
            else:
                serial_data = b"0"
            serial_list.append(bytes(serial_data))
            
            serialized = bytearray()  
            serialized.extend(byte_encode(serial_list[0]))
            for entry in serial_list[1:]:
                serialized.extend(b"\n")
                serialized.extend(byte_encode(entry))

            final = b"\n" + byte_encode(bytes(serialized)) + b"\n"
            return final
        if self.encode_type == EncodeType.JSON:
            payload = {
                "version": self.version,
                "request": self.request.value,
                "status": self.status.value,
                "sequence": self.sequence,
                "user": self.user,
                "datalen": self.datalen,
                "data": self.data
            }
            final = json.dumps(payload).encode("utf-8")
            return final

    def deserialize(self, input : bytes):
        '''
        update the object with the arguments provided in deserialize by reversing
        the steps used to serialize
        '''

        if self.encode_type == EncodeType.CUSTOM:
            if input[0] != ord("\n") or input[-1] != ord("\n"):
                raise Exception("Invalid encoding: Newline Wrapper Missing")
        
            input = input[1:-1]
            input = byte_decode(input)
            lines = input.split(b"\n")

            self.version = (byte_decode(lines[0]).decode("utf-8"))
            if self.version != CURRENT_VERSION:
                raise Exception("Invalid Encoding Version")

            if len(lines) != 7:
                raise Exception("Invalid encoding: Incorrect Fields")

            self.request = Request(int(byte_decode(lines[1]).decode("utf-8")))
            self.status = Status(int(byte_decode(lines[2]).decode("utf-8")))
            self.sequence = int(byte_decode(lines[3]).decode("utf-8"))
            self.user = byte_decode(lines[4]).decode("utf-8")
            self.datalen = int(byte_decode(lines[5]).decode("utf-8"))
            self.data = []

            if self.datalen == 0:
                if lines[6] != b"0":
                    raise Exception("Invalid encoding: Incorrect Fields")
            else:
                data = byte_decode(lines[6])
                data = data.split(b"\n")
                if len(data) != self.datalen:
                    raise Exception("Invalide encoding: Incorrect Data")
                for item in data:
                    self.data.append(byte_decode(item).decode("utf-8"))
                    
        elif self.encode_type == EncodeType.JSON:
            data = json.loads(input.decode("utf-8"))
            self.version = data["version"]
            if self.version != CURRENT_VERSION:
                raise Exception("Invalid Encoding Version")
            self.request = Request(data["request"])
            self.status = Status(data["status"])
            self.sequence = data["sequence"]
            self.user = data["user"]
            self.datalen = data["datalen"]
            self.data = data["data"]

        self.typecheck()

    # extract a single communication from raw bytes from the socket
    @staticmethod
    def get_one(input : bytes) -> tuple[bytes, bytes]:
        if not input or input == b"":
            return (b"",b"")
        if ENCODE_TYPE == EncodeType.CUSTOM:
            if input[0] != ord("\n"):
                raise Exception("Invalid Initial Byte")
            split_point = input.find(b"\n\n")
            if split_point == -1:
                if input[-1] == ord(b"\n"):
                    return (input, b"")
                else:
                    return (b"", input)
            else:
                first = input[:split_point + 1]
                rest = input[split_point + 1:]
                return first, rest
        elif ENCODE_TYPE == EncodeType.JSON:
            if input[0] != ord("{"):
                raise Exception("Invalid Initial Byte")
            depth = 0
            for i, byte in enumerate(input):
                char = chr(byte)
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                if depth == 0:
                    return (input[:i+1], input[i+1:])
            return (b"", input)
    
    # Useful for logging and debugging
    def to_string(self):
        return (f"\nDataObject uses {self.encode_type}, and contains:\n" +
                f"\t{self.request}\n" +
                f"\t{self.status}\n" +
                f"\tSequence: {self.sequence}\n" +
                f"\tUser: {self.user}\n" +
                f"\tData Length: {self.datalen}\n" +
                f"\tData: {self.data}\n")

class MessageObject:
    def __init__(self, 
                 method : Literal["args", "serial", "tuple"] = "args", 
                 serial : bytes = b"", 
                 tuple : tuple[int, str, str, str, int, str, str] = None,
                 id : int = 0,
                 sender : str = "",
                 recipient : str = "",
                 time : str = "",
                 read : bool = False,
                 subject : str = "",
                 body : str = ""):
        self.encode_type = ENCODE_TYPE
        self.version = CURRENT_VERSION
        if method == "tuple" and tuple != None:
            self.id = int(tuple[0])
            self.sender = tuple[1]
            self.recipient = tuple[2]
            self.time_sent = tuple[3]
            self.read = bool(tuple[4])
            self.subject = tuple[5]
            self.body = tuple[6]
            self.typecheck()
        elif method == "serial" and serial != None:   
            self.deserialize(serial)
            self.typecheck()
        elif method == "args":
            self.id = id
            self.sender = sender
            self.recipient = recipient
            self.time_sent = time
            self.read = read
            self.subject = subject
            self.body  = body
            self.typecheck()
        else:
            raise Exception("Invalid MessageObject Instantiation Method")
    
    def typecheck(self):
        '''
        Checks typing and basic assertions for each property
        '''       
        if not self.encode_type or not isinstance(self.encode_type, EncodeType):
            raise Exception("Invalid MessageObject encoding method Detected")
        if not self.version or not isinstance(self.version, str):
            raise Exception("Invalid MessageObject version Detected")
        if self.id == None or not isinstance(self.id, int):
            raise Exception("Invalid MessageObject id Detected")
        if self.sender == None or not isinstance(self.sender, str) or len(self.sender) < 1:
            raise Exception("Invalid MessageObject sender Detected")
        if self.recipient == None or not isinstance(self.recipient, str) or len(self.recipient) < 1:
            raise Exception("Invalid MessageObject recipient Detected")
        if self.time_sent == None or not isinstance(self.time_sent, str):
            raise Exception("Invalid MessageObject time Detected")
        if self.read == None or not isinstance(self.read, bool):
            raise Exception("Invalid MessageObject read Detected")
        if self.subject == None or not isinstance(self.subject, str):
            raise Exception("Invalid MessageObject subject Detected")
        if self.body == None or not isinstance(self.body, str):
            raise Exception("Invalid MessageObject body Detected")

    
    def update(self, 
                 method : Literal["args", "serial", "tuple"] = "args", 
                 serial : bytes = b"", 
                 tuple : tuple[int, str, str, str, int, str, str] = None,
                 id : int = None,
                 sender : str = None,
                 recipient : str = None,
                 time_sent : str = None,
                 read : bool = None,
                 subject : str = None,
                 body : str = None):
        if method == "tuple" and tuple != None:
            self.id = int(tuple[0])
            self.sender = tuple[1]
            self.recipient = tuple[2]
            self.time_sent = tuple[3]
            self.read = bool(tuple[4])
            self.subject = tuple[5]
            self.body = tuple[6]
            self.typecheck()
        if method == "serial":
            self.deserialize(serial)
            self.typecheck()
        elif method == "args":
            self.id = id if id != None else self.id
            self.sender = sender if sender != None else self.sender
            self.recipient = recipient if recipient != None else self.recipient
            self.time_sent = time_sent if time_sent != None else self.time_sent
            self.read = read if read != None else self.read
            self.subject = subject if subject != None else self.subject
            self.body = body if body != None else self.body
            self.typecheck()
        else:
            raise Exception("Invalid DataObject Update Method")
    

    def serialize(self):
        '''
        Serialize the object first removing "\n" from each field via encode, 
        joining feilds with "\n", removing "\n" once again via encode,
        then surrounding the entire bytestring with "\n"
        '''
        self.typecheck()

        if self.encode_type == EncodeType.CUSTOM:
            serial_list = [
                self.version.encode("utf-8"),
                str(self.id).encode("utf-8"),
                self.sender.encode("utf-8"),
                self.recipient.encode("utf-8"),
                self.time_sent.encode("utf-8"),
                str(1 if self.read else 0).encode("utf-8"),
                self.subject.encode("utf-8"),
                self.body.encode("utf-8")
            ]
            
            serialized = bytearray()  
            serialized.extend(byte_encode(serial_list[0]))
            for entry in serial_list[1:]:
                serialized.extend(b"\n")
                serialized.extend(byte_encode(entry))

            final = b"\n" + byte_encode(bytes(serialized)) + b"\n"
            return final
        if self.encode_type == EncodeType.JSON:
            payload = {
                "version": self.version,
                "id": self.id,
                "sender": self.sender,
                "recipient": self.recipient,
                "time_sent": self.time_sent,
                "read": self.read,
                "subject": self.subject,
                "body": self.body
            }
            final = json.dumps(payload).encode("utf-8")
            return final

    def deserialize(self, input : bytes):
        '''
        update the object with the arguments provided in deserialize by reversing
        the steps used to serialize
        '''

        if self.encode_type == EncodeType.CUSTOM:
            if input[0] != ord("\n") or input[-1] != ord("\n"):
                raise Exception("Invalid encoding: Newline Wrapper Missing")
            
            input = input[1:-1]
            input = byte_decode(input)
            lines = input.split(b"\n")
            
            self.version = (lines[0].decode("utf-8"))
            if self.version != CURRENT_VERSION:
                raise Exception("Invalid Encoding Version")
            
            if len(lines) != 8:
                raise Exception("Invalid encoding: Incorrect Fields")
            
            self.id = int(lines[1].decode("utf-8"))
            self.sender = byte_decode(lines[2]).decode("utf-8")
            self.recipient = byte_decode(lines[3]).decode("utf-8")
            self.time_sent = byte_decode(lines[4]).decode("utf-8")
            self.read = False if lines[5].decode("utf-8") == "0" else True
            self.subject = byte_decode(lines[6]).decode("utf-8")
            self.body  = byte_decode(lines[7]).decode("utf-8")
            print(f"Lines is {lines[7]}, decoded is {self.body}")
                    
        elif self.encode_type == EncodeType.JSON:
            data = json.loads(input.decode("utf-8"))
            self.version = data["version"]
            if self.version != CURRENT_VERSION:
                raise Exception("Invalid Encoding Version")
            self.id = data["id"]
            self.sender = data["sender"]
            self.recipient = data["recipient"]
            self.time_sent = data["time_sent"]
            self.read = data["read"]
            self.subject = data["subject"]
            self.body = data["body"]

        self.typecheck()
    
    # Given SQLlite3 inserts messages into the database as a tuple, 
    # it is easier to be able to directly create this tuple with a built-in function
    def to_sql_tuple(self) -> tuple[str, str, str, int, str, str]:
        return (self.sender, self.recipient, self.time_sent, int(self.read), self.subject, self.body)
    
    # Useful for logging and debugging
    def to_string(self):
        return (f"\nMessageObject uses {self.encode_type}, and contains:\n" +
                f"\tID: {self.id}\n"
                f"\tFrom: {self.sender}\n" +
                f"\tTo: {self.recipient}\n" +
                f"\tTime Sent: {self.time_sent}\n" +
                f"\tIs Read: {self.read}\n" +
                f"\tSubject: {self.subject}\n" +
                f"\tBody: {self.body}\n")