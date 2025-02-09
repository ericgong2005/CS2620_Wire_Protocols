from collections import deque

class SelectorData:
    def __init__(self, source : str):
        self.source = source
        self.received = deque()
        self.send = deque()
