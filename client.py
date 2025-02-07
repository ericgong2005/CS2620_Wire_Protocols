import socket
import sys

# run python client.py 

def start(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, int(port)))
        while True:
            message = input("Enter a message to send to the server: ")
            if message == "exit":
                break
            message = message.encode("utf-8")
            s.sendall(message)
            data = s.recv(1024)
            data = data.decode("utf-8")
            print(f"Received: {data}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py HOSTNAME PORTNAME")
        exit(1)
    
    start(sys.argv[1], sys.argv[2])
