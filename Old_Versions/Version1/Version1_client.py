import socket
import sys

# run python client.py HOSTNAME PORTNAME

def client_user(server_socket):
    while True:
        message = input("Enter a message to send to the server: ")
        if message == "exit":
            break
        message = message.encode("utf-8")
        server_socket.sendall(message)
        data = server_socket.recv(1024)
        data = data.decode("utf-8")
        print(f"Received: {data}")

def client_login(server_socket):
    username = ""
    while True:
        username = input("Enter Username: ")
        message = ("username " + username).encode("utf-8")
        server_socket.sendall(message)

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data = data.decode("utf-8")
        print(f"Recieved {data}")
        if data == "Enter Password":
            break
        elif data == "No User":
            print("No such username exists")
        else:
            print("Error")
    
    password = ""
    while True:
        password = input("Enter Password: ")
        message = ("password " + password).encode("utf-8")
        server_socket.sendall(message)

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data = data.decode("utf-8")
        print(f"Recieved {data}")
        if data == "Logged In":
            print("Logged In")
            client_user(server_socket)
            break
        elif data == "Wrong Password":
            print("Wrong Password")
        else:
            print("Error")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py HOSTNAME PORTNAME")
        exit(1)
    host, port = sys.argv[1], int(sys.argv[2])

    # Connect to the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, int(port)))

    # Start the login process
    client_login(server_socket)

    server_socket.close()
