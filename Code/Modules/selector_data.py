from queue import Queue

class SelectorData:
    def __init__(self, source : str, address : any = None):
        self.source : str = source
        self.address = address
        self.inbound : Queue[bytes] = Queue()
        self.outbound : Queue[bytes] = Queue()
