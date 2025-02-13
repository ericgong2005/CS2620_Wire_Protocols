import time

from Modules.Flags import Request, Status, EncodeType
from Modules.Constants import ENCODE_TYPE
from Modules.DataObjects import DataObject, MessageObject

from Analytics.Analytics_test_data import SHORT_ENGLISH_MESSAGE, SHORT_CHINESE_MESSAGE


# def timer(func):
#     """Decorator that times how long a function takes to run."""
#     def wrapper(*args, **kwargs):
#         start_time = time.perf_counter()  # Start high-resolution timer
#         result = func(*args, **kwargs)
#         end_time = time.perf_counter()    # End high-resolution timer
#         elapsed_time = end_time - start_time
#         print(f"{func.__name__} executed in {elapsed_time:.10f} seconds")
#         return result
#     return wrapper

names = ["SHORT_ENGLISH_MESSAGE", "SHORT_CHINESE_MESSAGE"]
messages = [SHORT_ENGLISH_MESSAGE, SHORT_CHINESE_MESSAGE]
for index, message in enumerate(messages):
    total_time = 0
    for _i in range(1000):
        start_time = time.perf_counter()
        encoded = MessageObject(sender="Sender", recipient="Recipient", subject=str(message), body=str(message)).serialize()
        end_time = time.perf_counter()
        total_time += (end_time - start_time)
    print(f"MessageObject\t{ENCODE_TYPE}\t{names[index]}\t{total_time}\t{len(encoded)}")

    total_time = 0
    for _i in range(1000):
        start_time = time.perf_counter()
        encoded = DataObject(datalen=10, data=([message]*10)).serialize()
        end_time = time.perf_counter()
        total_time += (end_time - start_time)
    print(f"DataObject\t{ENCODE_TYPE}\t{names[index]}\t{total_time}\t{len(encoded)}")

names = ["LONG_ENGLISH_MESSAGE", "LONG_CHINESE_MESSAGE"]
for index, message in enumerate(messages):
    total_time = 0
    for _i in range(100):
        start_time = time.perf_counter()
        encoded = MessageObject(sender="Sender", recipient="Recipient", subject=str([message]*10), body=str([message]*10)).serialize()
        end_time = time.perf_counter()
        total_time += (end_time - start_time)
    print(f"MessageObject\t{ENCODE_TYPE}\t{names[index]}\t{total_time}\t{len(encoded)}")

    total_time = 0
    for _i in range(100):
        start_time = time.perf_counter()
        encoded = DataObject(datalen=100, data=([message]*100)).serialize()
        end_time = time.perf_counter()
        total_time += (end_time - start_time)
    print(f"DataObject\t{ENCODE_TYPE}\t{names[index]}\t{total_time}\t{len(encoded)}")

'''
Data:
object, encoding, message name, average time, message length
MessageObject   EncodeType.CUSTOM       SHORT_ENGLISH_MESSAGE   0.2842270717956126      2408
DataObject      EncodeType.CUSTOM       SHORT_ENGLISH_MESSAGE   2.0218134138267487      12078
MessageObject   EncodeType.CUSTOM       SHORT_CHINESE_MESSAGE   0.3299366927240044      3028
DataObject      EncodeType.CUSTOM       SHORT_CHINESE_MESSAGE   2.4650634832214564      15738
MessageObject   EncodeType.CUSTOM       LONG_ENGLISH_MESSAGE    0.2725707010831684      23516
DataObject      EncodeType.CUSTOM       LONG_ENGLISH_MESSAGE    1.9951112461276352      120529
MessageObject   EncodeType.CUSTOM       LONG_CHINESE_MESSAGE    0.32562241377308965     28596
DataObject      EncodeType.CUSTOM       LONG_CHINESE_MESSAGE    2.4440256166271865      157129
MessageObject   EncodeType.JSON         SHORT_ENGLISH_MESSAGE   0.010205461643636227    2472
DataObject      EncodeType.JSON         SHORT_ENGLISH_MESSAGE   0.03329324838705361     11846
MessageObject   EncodeType.JSON         SHORT_CHINESE_MESSAGE   0.0070371965412050486   5428
DataObject      EncodeType.JSON         SHORT_CHINESE_MESSAGE   0.023492811480537057    26626
MessageObject   EncodeType.JSON         LONG_ENGLISH_MESSAGE    0.012835951754823327    23972
DataObject      EncodeType.JSON         LONG_ENGLISH_MESSAGE    0.026977451983839273    117507
MessageObject   EncodeType.JSON         LONG_CHINESE_MESSAGE    0.01032058009877801     54612
DataObject      EncodeType.JSON         LONG_CHINESE_MESSAGE    0.02135837497189641     265307
'''