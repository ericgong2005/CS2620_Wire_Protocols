from queue import Queue

class SelectorData:
    def __init__(self, source : str, address : any = None):
        self.source : str = source
        self.address = address
        self.inbound : bytes = b""
        self.outbound : Queue[bytes] = Queue()
