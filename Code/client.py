import socket
import sys
import selectors
from datetime import datetime, timezone

from Modules.Flags import Request, Status
from Modules.DataObjects import DataObject, MessageObject
from Modules.selector_data import SelectorData

# run python client.py HOSTNAME PORTNAME

def client_user(server_socket, username):
    data = server_socket.recv(1024)
    if not data:
            print("Connection closed by the server.")
            return
    response = DataObject(method="serial", serial=data)
    if response.request != Request.CONFIRM_LOGIN:
        print("Unexpected Communication, Login Failed")
        return
    if response.status == Status.SUCCESS:
        print("Logged In")
    elif response.status == Status.MATCH:
        print("Already Logged In Elsewhere")
        return
    else:
        print("Login Failed")
        return
    
    # Use selectors to allow for polling instead of blocking
    client_selector = selectors.DefaultSelector()
    client_selector.register(server_socket, selectors.EVENT_READ, data=SelectorData("User"))
    server_socket.setblocking(False)

    while True:
        # Send user input to database
        command = input(f"Enter a message as User {username}: ")
        if command == "exit":
            break
        lines = command.split()
        request = DataObject(user=username)
        if lines[0] == "get":
            request.update(request=Request.GET_ONLINE_USERS)
        elif lines[0] == "message":
            recipient = input("Send Message To: ")
            subject = input("Enter Message Subject: ")
            body = input("Enter Message Body: ")
            current_time = datetime.now(timezone.utc)
            iso_time = current_time.isoformat(timespec='seconds')
            message = MessageObject(sender=username, recipient=recipient, time=iso_time, subject=subject, body=body)
            message_string = message.serialize().decode("utf-8")
            # print(f"Sending Message: {message.to_string()}")
            request.update(request=Request.SEND_MESSAGE, datalen=1, data=[message_string])
        else:
            request.update(request=Request.ALERT_MESSAGE, datalen=1, data=[command])

        server_socket.sendall(request.serialize())

        # Get response(s)
        events = client_selector.select(timeout=None)
        for key, mask in events:
            if mask & selectors.EVENT_READ:
                while True:
                    try:
                        data = key.fileobj.recv(1024)
                        if not data:
                            print("Connection closed by the server.")
                            return
                        response = DataObject(method="serial", serial=data)
                        print(response.to_string()) 
                    except BlockingIOError:
                        break
                    

def client_create_user(server_socket):
    username = ""
    while True:
        print("Create New User:")
        username = input("Enter Username: ")
        password = input("Enter Password: ")
        confirm_password = input("Confirm Password: ")
        if password == confirm_password:
            request = DataObject(request=Request.CREATE_USER, datalen=2, data=[username, password])
            server_socket.sendall(request.serialize())
        else:
            continue

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        response = DataObject(method="serial", serial=data)
        # print(f"Recieved {response.to_string()}")
        if response.status == Status.SUCCESS:
            print(f"Created User with Username: {username}, Password: {password}")
            return
        elif response.status == Status.MATCH:
            print("User Exists.")
            return
        else:
            print("Error")

def client_login(server_socket):
    username = ""
    while True:
        print("Login:")
        username = input("Enter Username: ")
        request = DataObject(request=Request.CHECK_USERNAME, datalen=1, data=[username])
        server_socket.sendall(request.serialize())

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        response = DataObject(method="serial", serial=data)
        # print(f"Recieved {response.to_string()}")
        if response.status == Status.MATCH:
            break
        elif response.status == Status.NO_MATCH:
            print("No such username exists")
            client_create_user(server_socket)
        else:
            print("Error")
    
    password = ""
    while True:
        password = input("Enter Password: ")
        request = DataObject(request=Request.CHECK_PASSWORD, datalen = 2, data = [username, password])
        server_socket.sendall(request.serialize())

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        response = DataObject(method="serial", serial=data)
        if response.status == Status.MATCH:
            print("Logging In")
            client_user(server_socket, username)
            break
        elif response.status == Status.NO_MATCH:
            print("Wrong Password")
        else:
            print("Error")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py HOSTNAME PORTNAME")
        exit(1)
    host, port = sys.argv[1], int(sys.argv[2])

    while True:
        # Connect to the server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((host, int(port)))

        # Start the login process
        client_login(server_socket)

        server_socket.close()
