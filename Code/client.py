import socket
import sys

# run python client.py HOSTNAME PORTNAME

def client_user(server_socket, username):
    while True:
        message = input(f"Enter a message as User {username}: ")
        if message == "exit":
            break
        message = message.encode("utf-8")
        server_socket.sendall(message)
        data = server_socket.recv(1024)
        data = data.decode("utf-8")
        print(f"Received: {data}")

def client_create_user(server_socket):
    username = ""
    while True:
        print("Create New User:")
        username = input("Enter Username: ")
        password = input("Enter Password: ")
        confirm_password = input("Confirm Password: ")
        if password == confirm_password:
            message = ("add " + username + " " + password).encode("utf-8")
            server_socket.sendall(message)

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data = data.decode("utf-8")
        print(f"Recieved {data}")
        if data == "Success":
            print(f"Created User with Username: {username}, Password: {password}")
            return
        elif data == "Exists":
            print("User Exists.")
            return
        elif data == "Fail":
            print("Failed to create new user. Try again.")
        else:
            print("Error")

def client_login(server_socket):
    username = ""
    while True:
        print("Login:")
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
            client_create_user(server_socket)
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
            client_user(server_socket, username)
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
