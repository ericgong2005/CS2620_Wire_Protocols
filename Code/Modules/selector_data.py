from queue import Queue

class SelectorData:
    def __init__(self, source : str):
        self.source : str = source
        self.inbound : Queue[bytes] = Queue()
        self.outbound : Queue[bytes] = Queue()
