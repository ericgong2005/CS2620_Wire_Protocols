#!/usr/bin/env python3
import os
import socket
import sys
import multiprocessing as mp
import selectors
import types

from Modules.database_manager import DatabaseManager, QueryObject, ResponseObject
from Modules.constants import DB, Status

def database_query(db, selector, online_username, online_address, key, mask):
    socket = key.fileobj
    data = key.data
    address_string = f"{data.address}"
    if mask & selectors.EVENT_READ:
        recieve = socket.recv(1024)
        if recieve:
            print(f"Database recieved Request: {recieve.decode("utf-8")}")
            request = QueryObject(None, None, None, None)
            request.deserialize(recieve.decode("utf-8"))
            response = ResponseObject(None, None)
            print(f"Database recieved Request: {request.to_string()}")
            if request.request == DB.LOGIN:
                if request.username in online_username:
                    response.update(Status.DUPLICATE, None)
                else:
                    online_username[request.username] = key
                    online_address[address_string] = request.username
                    response.update(Status.SUCCESS, None)
            elif request.request == DB.CURRENT_USERS:
                response.update(Status.SUCCESS, list(online_username.keys()))
            elif request.request == DB.NOTIFY:
                target_username = request.data[0]
                if target_username in online_username:
                    target_key = online_username[target_username]
                    if target_key.data.outb != b"":
                        raise Exception("Mismanaged client connection")
                    response.update(Status.ALERT, [request.username])
                    target_key.data.outb += response.serialize().encode("utf-8")
                    response.update(Status.SUCCESS, None)
                else:
                    response.update(Status.FAIL, None)
            else:
                status, db_data = db.handler(request)
                print(f"Handler Responds with {status} {db_data}")
                response.update(status, db_data if db_data else None) 
            data.outb += response.serialize().encode("utf-8")
        else:
            print(f"Database closing connection to {data.address}")
            if address_string in online_address:
                del online_username[online_address[address_string]]
                del online_address[address_string]
            selector.unregister(socket)
            socket.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            socket.sendall(data.outb)
            print(f"Database responds with: {data.outb.decode("utf-8")}")
            data.outb = b""
    
def database_process(host, database_port):
    """
    Handle all requests to the database
    """

    print(f"Database process {os.getpid()} started")

    database_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    database_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    database_socket.bind((host, database_port))
    database_socket.listen(5)
    print(f"Database listening on {(host, database_port)}")
    database_socket.setblocking(False)

    selector = selectors.DefaultSelector()
    selector.register(database_socket, selectors.EVENT_READ, data=None)

    db = DatabaseManager()

    # Add some fake users in case the db is empty
    db.insert_user("a", "b")
    db.insert_user("abcd", "1234")

    # bi-directional {username : address} and {address : username} for who is online
    online_username = {}
    online_address = {}

    try:
        while True:
            events = selector.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    connection, address = key.fileobj.accept()
                    print(f"Database accepted connection from {address}")
                    connection.setblocking(False)
                    data = types.SimpleNamespace(address=address, inb=b"", outb=b"")
                    events = selectors.EVENT_READ | selectors.EVENT_WRITE
                    selector.register(connection, events, data=data)
                else:
                    database_query(db, selector, online_username, online_address, key, mask)
    except Exception as e:
        print(f"Database process encountered error {e}")
    finally:
        print("Closing Database Process")
        selector.close()


def user_process(client_connection, address, database, user_start, username) :
    """
    Handle client connection normal user activity
    """
    user_start.set()
    
    database_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    database_connection.connect(database)

    user_sockets = [client_connection, database_connection]

    logged_in = False
    try:
        print(f"User process {os.getpid()} handling connection from {address}")

        request = QueryObject(DB.LOGIN, username, os.getpid(), None)
        database_connection.sendall(request.serialize().encode("utf-8"))
        database_response = ResponseObject(None, None)
        database_raw = database_connection.recv(1024)
        if not database_raw:
            raise Exception("Connection Closed By Server")
        if not database_response.deserialize(database_raw.decode("utf-8")) == Status.SUCCESS:
            raise Exception("Parsing Failed")
        print(f"User Process {os.getpid()} recieved {database_raw.decode("utf-8")}")
        if database_response.status == Status.SUCCESS:
            logged_in = True
            response = "Logged In"
        elif database_response.status == Status.DUPLICATE:
            response = "Duplicate"
        else:
            response = "Failed"
        
        client_connection.sendall(response.encode("utf-8"))

        while logged_in:
            data = client_connection.recv(1024)
            print(f"User process {os.getpid()} got data {data}")

            # Check if connection closed by client
            if not data:
                break  
            data = data.decode("utf-8")
            words = data.split()
            if words[0] == "get":
                request = QueryObject(DB.CURRENT_USERS, username, os.getpid(), None)
                database_connection.sendall(request.serialize().encode("utf-8"))
                database_response = ResponseObject(None, None)
                database_raw = database_connection.recv(1024)
                if not database_raw:
                    raise Exception("Connection Closed By Server")
                if not database_response.deserialize(database_raw.decode("utf-8")) == Status.SUCCESS:
                    raise Exception("Parsing Failed")
                print(f"User Process {os.getpid()} recieved {database_raw.decode("utf-8")}")
                if(database_response.status == Status.SUCCESS):
                    response = f"Users: {database_response.data}"
                else:
                    response = "Failed to Retrieve Active Users"
            elif words[0] == "ping":
                request = QueryObject(DB.NOTIFY, username, os.getpid(), [words[1]])
                database_connection.sendall(request.serialize().encode("utf-8"))
                database_response = ResponseObject(None, None)
                database_raw = database_connection.recv(1024)
                if not database_raw:
                    raise Exception("Connection Closed By Server")
                if not database_response.deserialize(database_raw.decode("utf-8")) == Status.SUCCESS:
                    raise Exception("Parsing Failed")
                print(f"User Process {os.getpid()} recieved {database_raw.decode("utf-8")}")
                if(database_response.status == Status.SUCCESS):
                    response = "Ping Sent"
                else:
                    response = "Failed to Send Ping"
            else:
                response = f"Success: {data}"

            client_connection.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in User process {os.getpid()}:", e)
    finally:
        if logged_in:
            request = QueryObject(DB.LOGOUT, username, os.getpid(), None)
            database_connection.sendall(request.serialize().encode("utf-8"))
        client_connection.close()
        database_connection.close()
        print(f"User process {os.getpid()} closing connection from {address}")

def login_process(client_connection, address, database):
    """
    Handle client connection login
    """

    username = ""
    
    database_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    database_socket.connect(database)

    try:
        print(f"Login process {os.getpid()} handling connection from {address}")

        while True:
            data = client_connection.recv(1024)
            print(f"Login process {os.getpid()} got data {data}")

            # Check if connection closed by client
            if not data:
                break  

            words = data.decode("utf-8").split()
            if not words:
                continue
            elif words[0] == "username":
                request = QueryObject(DB.CHECK_USERNAME, None, os.getpid(), [words[1]])
                database_socket.sendall(request.serialize().encode("utf-8"))
                database_response = ResponseObject(None, None)
                database_raw = database_socket.recv(1024)
                print(f"Login Process {os.getpid()} recieved from database: {database_raw}")
                if not database_raw:
                    print("Connection closed by the server.")
                    break
                if not database_response.deserialize(database_raw.decode("utf-8")) == Status.SUCCESS:
                    print("Parsing Failed")
                    break
                print(f"Login Process {os.getpid()} parses to: {database_raw.decode("utf-8")}")
                if database_response.status == Status.SUCCESS and database_response.data[0] == words[1]:
                    username = database_response.data[0]
                    response = "Enter Password"
                else:
                    response = "No User"
            elif words[0] == "password":
                if not username:
                    response = "Enter Username"
                else:
                    request = QueryObject(DB.CHECK_PASSWORD, None, os.getpid(), [username, words[1]])
                    database_socket.sendall(request.serialize().encode("utf-8"))
                    database_response = ResponseObject(None, None)
                    try:
                        database_raw = database_socket.recv(1024)
                        if not database_raw:
                            print("Connection closed by the server.")
                            break
                        if not database_response.deserialize(database_raw.decode("utf-8")) == Status.SUCCESS:
                            print("Parsing Failed")
                            break
                        print(f"Login Process {os.getpid()} recieved from database: {database_raw.decode("utf-8")}")
                    except Exception as e:
                        print("User process failed to receive response from database due to", e)
                        break
                    if database_response.status == Status.SUCCESS and database_response.data[0] == username:
                        user_start =  mp.Event()
                        client_user = mp.Process(target=user_process, args=(client_connection, address, database, user_start, username))
                        client_user.start()
                        user_start.wait()
                        response = "Logged In"
                        client_connection.sendall(response.encode("utf-8"))
                        break
                    else:
                        response = "Wrong Password"
            elif words[0] == "add":
                if not words[1] or not words[2]:
                    response = "Fail"
                else:
                    request = QueryObject(DB.ADD_USER, None, os.getpid(), [words[1], words[2]])
                    database_socket.sendall(request.serialize().encode("utf-8"))
                    database_response = ResponseObject(None, None)
                    try:
                        database_raw = database_socket.recv(1024)
                        if not database_raw:
                            print("Connection closed by the server.")
                            break
                        if not database_response.deserialize(database_raw.decode("utf-8")) == Status.SUCCESS:
                            print("Parsing Failed")
                            break
                        print(f"Login Process {os.getpid()} recieved from database: {database_raw.decode("utf-8")}")
                    except Exception as e:
                        print("User process failed to receive response from database due to", e)
                        break
                    if database_response.status == Status.SUCCESS:
                        response = "Success"
                    elif database_response.status == Status.DUPLICATE:
                        response = "Exists"
                    else:
                        response = "Fail"          
            client_connection.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in login process {os.getpid()}:", e)
    finally:
        client_connection.close()
        database_socket.close() 
        print(f"Login process {os.getpid()} closing connection from {address}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python server.py HOSTNAME DAEMON_PORTNAME DATABASE_PORTNAME")
        sys.exit(1)
    host, daemon_port, database_port = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

    # Set the child creation type to spawn to support windows
    mp.set_start_method('spawn')

    # Set up the database process
    database = mp.Process(target=database_process, args=(host, database_port,))
    database.start()

    # Set up socket to listen for connection requests
    connect_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_request.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connect_request.bind((host, daemon_port))
    connect_request.listen(5)
    print(f"Daemon listening on {(host, daemon_port)}")

    while True:
        try:
            client_connection, address = connect_request.accept()

            # Fork a child process to handle client login
            client_login = mp.Process(target=login_process, args=(client_connection, address, (host, database_port)))
            client_login.start()

            # Close client connection on daemon end
            client_connection.close()
        except KeyboardInterrupt:
            print("Shutting Down: KeyboardInterrupt")
            break
        except Exception as e:
            print("Error:", e)
    
    connect_request.close()
