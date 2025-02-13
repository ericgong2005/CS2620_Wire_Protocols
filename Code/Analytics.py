'''
Generate various timing and message size metrics. 
Note that we do not collect data on passing JSON encoded messages
through the socket, for datalen > 250 due to it requiring significant 
time to do so (On the order of 45 seconds)
'''

import time
import socket
import sys

import pandas as pd
import matplotlib.pyplot as plt

from Modules.Flags import Request, Status, EncodeType
from Modules.Constants import ENCODE_TYPE
from Modules.DataObjects import DataObject, MessageObject

from Analytics.Analytics_test_data import SHORT_ENGLISH_MESSAGE, SHORT_CHINESE_MESSAGE

OUTPUT_FILE = "Analytics/results.txt"
PLOT_PATH = "Analytics/Plots/"

def generate_timing(host, port):
    '''
    Establish a test socket for sending messages, and check how long it takes to send 
    messages of various length
    '''
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)

    send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send.connect((host, int(port)))

    recieve, _address = server.accept()

    with open("Analytics/results.txt", "a") as file:
        file.write(f"LENGTH\tENCODING_TYPE\tMESSAGE_TYPE\tSEND_TIME\tRECIEVE_TIME\tMESSAGE_SIZE\n")

    messages = [SHORT_ENGLISH_MESSAGE, SHORT_CHINESE_MESSAGE]
    names = ["ENGLISH_MESSAGE", "CHINESE_MESSAGE"]
    for datalen in range(10, 510, 10):
        for index, message in enumerate(messages):
            start_time = time.perf_counter()
            data = []
            for _i in range(datalen):
                data.append(MessageObject(sender="Sender", recipient="Recipient", subject=message, body=message).serialize().decode("utf-8"))
            send_out = DataObject(request=Request.SEND_MESSAGE, datalen=datalen, data=data).serialize()
            send.sendall(send_out) # Comment out this line for large JSON tests
            send_time = time.perf_counter()
            # Comment out the following for large JSON tests
            data_buffer = b""
            while True:
                data = recieve.recv(1024)
                if not data:
                    raise Exception("Socket Closed")
                data_buffer += data
                serial, data_buffer = DataObject.get_one(data_buffer)
                if serial != b"":
                    response = DataObject(method="serial", serial=serial)
                    break
            end_time = time.perf_counter()
            with open(OUTPUT_FILE, "a") as file:
                # Change end_time - send_time to -1.0 for large JSON tests
                file.write(f"{datalen}\t{ENCODE_TYPE}\t{names[index]}\t{send_time - start_time}\t{end_time - send_time}\t{len(send_out)}\n")

def plot_graph(data, metric, message_type, ylabel, title, filename):
    plt.figure(figsize=(8, 6))
    if metric == 'RECIEVE_TIME':
        data = data[data['RECIEVE_TIME'] != -1.0] # Use -1 to mark skipped trials
    for encoding in ['EncodeType.CUSTOM', 'EncodeType.JSON']:
        # Filter by message type and encoding type
        subset = data[(data['MESSAGE_TYPE'] == message_type) &
                      (data['ENCODING_TYPE'] == encoding)]
        if not subset.empty:
            subset = subset.sort_values(by='LENGTH')
            plt.plot(subset['LENGTH'], subset[metric], marker='o', label=encoding)
    plt.xlabel('Number of MessageObjects in DataObject')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(PLOT_PATH + filename, format='png')
    plt.close()

def analyze_timing():
    data = pd.read_csv(OUTPUT_FILE, sep='\t')
    data['LENGTH'] = pd.to_numeric(data['LENGTH'])
    data['SEND_TIME'] = pd.to_numeric(data['SEND_TIME'])
    data['RECIEVE_TIME'] = pd.to_numeric(data['RECIEVE_TIME'])
    data['MESSAGE_SIZE'] = pd.to_numeric(data['MESSAGE_SIZE']) / 1024

    metric_label = {"SEND_TIME" : "Time to Serialize and Send message (seconds)", 
             "RECIEVE_TIME" : "Time to Recieve and Deserialize message (seconds)", 
             "MESSAGE_SIZE" : "Size of Serialized message (kB)"}
    language_label = {"ENGLISH_MESSAGE" : "English Messages", "CHINESE_MESSAGE" : "Chinese (Special Character) Messages"}

    for metric in ["SEND_TIME", "RECIEVE_TIME", "MESSAGE_SIZE"]:
        for language in ["ENGLISH_MESSAGE", "CHINESE_MESSAGE"]:
            plot_graph( data, metric, language,
                ylabel=f"{metric_label[metric]}",
                title=f"{metric_label[metric]} for\n{language_label[language]} as a function of the\nNumber of MessageObjects in the DataObject",
                filename=f"{language}_{metric}.png")

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "Generate":
        generate_timing(sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) == 2 and sys.argv[1] == "Analyze":
        analyze_timing()
    else:
        print("Usage: python Analytics.py Analyze OR python Analytics.py Generate HOSTNAME PORTNAME")
        sys.exit(1)
        
