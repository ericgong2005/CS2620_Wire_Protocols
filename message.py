import json

### MESSAGE CONSTANTS ###

# Operations
USERNAME = 1
PASSWORD = 2
MESSAGE = 3

class Message:

    def __init__(self, version, operation, data):
        self.version = version
        self.operation = operation
        self.data = data
    # system: e.g. "login successful"
    # login: username password(hashed) (separate?)
    # message: sender, recipient, time sent, subject, message
        
    def serialize(self, mode="custom"):
        """
        Serialize message
        """
        if mode == "custom":
            pass
        elif mode == "json":
            payload = {
                "version": self.version,
                "operation": self.operation,
                "data": self.data,
            }
            return json.dumps(payload)
        else:
            print("Serialization error")