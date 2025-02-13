'''
This file contains the SelectorData class used by the socket selectors implemented
in the database_process and user_process
'''

from queue import Queue

class SelectorData:
    def __init__(self, source : str, address : any = None):
        self.source : str = source
        self.address = address
        self.inbound : bytes = b""
        self.outbound : Queue[bytes] = Queue()
