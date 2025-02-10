#!/usr/bin/env python3
import os
import socket
import sys
import multiprocessing as mp
import selectors

from Modules.database_manager import DatabaseManager
from Modules.data_objects import QueryObject, ResponseObject
from Modules.selector_data import SelectorData
from Modules.constants import DB, Status

def database_request_handler(db : DatabaseManager, 
                             request : QueryObject, 
                             key : selectors.SelectorKey, 
                             online_username : dict[str, selectors.SelectorKey], 
                             online_address : dict[str, str]) -> ResponseObject:
    response = ResponseObject()
    address_string = f"{key.data.address}"
    if request.request == DB.LOGIN:
        if request.username in online_username:
            response.update(DB.LOGIN, Status.DUPLICATE)
        else:
            online_username[request.username] = key
            online_address[address_string] = request.username
            response.update(DB.LOGIN, Status.SUCCESS)
    elif request.request == DB.CURRENT_USERS:
        response.update(DB.CURRENT_USERS, Status.SUCCESS, list(online_username.keys()))
    elif request.request == DB.NOTIFY:
        target_username = request.data[0]
        if target_username in online_username:
            target_key = online_username[target_username]
            response.update(DB.NOTIFY, Status.ALERT, [request.username])
            target_key.data.outbound.put(response.serialize())
            response.update(DB.NOTIFY, Status.SUCCESS, None)
        else:
            response.update(DB.NOTIFY, Status.FAIL, None)
    else:
        status, db_data = db.handler(request)
        print(f"Handler Responds with {status} {db_data}")
        response.update(request.request, status, db_data if db_data else None) 
    return response

def database_process(host, database_port, database_start):
    """
    Handle all requests to the database
    """

    print(f"Database process {os.getpid()} started")

    database_start.set()

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
                if key.data is None: # Add new connection
                    connection, address = key.fileobj.accept()
                    print(f"Database accepted connection from {address}")
                    connection.setblocking(False)
                    events = selectors.EVENT_READ | selectors.EVENT_WRITE
                    selector.register(connection, events, data=SelectorData(f"{address}", address))
                else:
                    cur_socket = key.fileobj
                    address_string = f"{key.data.address}"
                    if mask & selectors.EVENT_READ:
                        recieve = cur_socket.recv(1024)
                        if recieve:
                            print(f"Database recieved Request: {recieve.decode("utf-8")}")
                            request = QueryObject()
                            request.deserialize(recieve)
                            print(f"Database recieved Request: {request.to_string()}")
                            response = database_request_handler(db, request, key, online_username, online_address)
                            key.data.outbound.put(response.serialize())
                        else:
                            print(f"Database closing connection to {key.data.address}")
                            if address_string in online_address:
                                del online_username[online_address[address_string]]
                                del online_address[address_string]
                            selector.unregister(cur_socket)
                            cur_socket.close()
                    if mask & selectors.EVENT_WRITE:
                        if not key.data.outbound.empty():
                            message = key.data.outbound.get()
                            cur_socket.sendall(message)
                            print(f"Database sent to {key.data.source}: {message.decode("utf-8")}")
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
    
    # Setup the connection to the database
    database_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        database_connection.connect(database)
    except Exception as e:
        print(f"Error in User process {os.getpid()} when connecting to database:", e)
        return

    # Set up the selector to switch between client and database communications
    user_selector = selectors.DefaultSelector()
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    user_selector.register(client_connection, events, data = SelectorData("client"))
    user_selector.register(database_connection, events, data = SelectorData("database"))

    keys = {key.data.source: key for key in user_selector.get_map().values()}

    # Send a message to the database, confirming Login
    try:
        request = QueryObject(DB.LOGIN, username, os.getpid())
        keys["database"].fileobj.sendall(request.serialize())
    except Exception as e:
        print(f"Error in User process {os.getpid()} when sending Login to database:", e)
        user_selector.close()
        return

    logged_in = False

    # Wait for confirmation of Login (Ignore all other communications until the login is confirmed)
    try:
        while not logged_in:
            events = user_selector.select(timeout=None)
            for key, mask in events:
                source = key.data.source
                if source == "database" and mask & selectors.EVENT_READ:
                    database_raw = keys["database"].fileobj.recv(1024)
                    if not database_raw:
                        raise Exception(f"Connection Closed By {source}")
                    database_response = ResponseObject()
                    status, remaining = database_response.deserialize(database_raw)
                    if status != Status.SUCCESS:
                        print("Parsing Failed")
                        break
                    print(f"User Process {os.getpid()} recieved {database_raw.decode("utf-8")}")
                    if database_response.request != DB.LOGIN:
                        continue
                    if database_response.status == Status.SUCCESS:
                        logged_in = True
                        response = "Logged In"
                    elif database_response.status == Status.DUPLICATE:
                        response = "Duplicate"
                    else:
                        response = "Failed"
                    keys["client"].fileobj.sendall(response.encode("utf-8"))
                    if not logged_in:
                        raise Exception(response)                
    except Exception as e:
        print(f"Error in User process {os.getpid()} when confirming login:", e)

    
    # Messages as usual
    try:
        while True:
            events = user_selector.select(timeout=None)
            for key, mask in events:
                source = key.data.source
                if source == "client":
                    if mask & selectors.EVENT_READ:
                        raw_client = keys["client"].fileobj.recv(1024)
                        if not raw_client:
                            raise Exception("Connection closed by client")
                        raw_client = raw_client.decode("utf-8")
                        words = raw_client.split()
                        if words[0] == "get":
                            request = QueryObject(DB.CURRENT_USERS, username, os.getpid(), None)
                            keys["database"].data.outbound.put(request.serialize())
                            print(f"{keys["database"].data.outbound.empty()} Outgoing to {source}")
                        elif words[0] == "ping":
                            request = QueryObject(DB.NOTIFY, username, os.getpid(), [words[1]])
                            keys["database"].data.outbound.put(request.serialize())
                            print(f"{keys["database"].data.outbound.empty()} Outgoing to {source}")
                        else:
                            response = f"Success: {raw_client}"
                            keys["client"].data.outbound.put(response.encode("utf-8"))
                            print(f"{keys["client"].data.outbound.empty()} Outgoing to {source}")
                    if mask & selectors.EVENT_WRITE and not key.data.outbound.empty():
                        message = key.data.outbound.get()
                        key.fileobj.sendall(message)
                        print(f"Sent from User process to client: {message}")
                if source == "database":
                    if mask & selectors.EVENT_READ:
                        database_response = ResponseObject()
                        database_raw = keys["database"].fileobj.recv(1024)
                        if not database_raw:
                            raise Exception("Connection Closed By Server")
                        
                        print(f"User Process {os.getpid()} recieved {database_raw.decode("utf-8")}")

                        if not key.data.inbound.empty():
                            prev = key.data.inbound.get()
                            prev = prev + database_raw
                            status, remaining = database_response.deserialize(prev)
                        else:
                            status, remaining = database_response.deserialize(database_raw)

                        while status == Status.SUCCESS:
                            print(database_response.to_string())
                            if database_response.request == DB.CURRENT_USERS:
                                if(database_response.status == Status.SUCCESS):
                                    response = f"Users: {database_response.data}"
                                else:
                                    response = "Failed to Retrieve Active Users"
                                keys["client"].data.outbound.put(response.encode("utf-8"))
                                print(f"{keys["client"].data.outbound.empty()} Outgoing to {source}")
                            if database_response.request == DB.NOTIFY:
                                if database_response.status == Status.ALERT:
                                    response = f"Ping from {database_response.data[0]}\n"
                                elif database_response.status == Status.SUCCESS:
                                    response = "Sent Ping"
                                else:
                                    response = "Failed to Send Ping"
                                keys["client"].data.outbound.put(response.encode("utf-8"))
                                print(f"{keys["client"].data.outbound.empty()} Outgoing to {source}")
                            status, remaining = database_response.deserialize(remaining)
                        
                        if remaining != b"":
                            key.data.inbound.put(remaining)

                    if mask & selectors.EVENT_WRITE and not key.data.outbound.empty():
                        message = key.data.outbound.get()
                        key.fileobj.sendall(message)
                        print(f"Sent from User process to database: {message}")
    except Exception as e:
        print(f"Error in User process {os.getpid()}:", e)
    finally:
        user_selector.close()
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
                database_socket.sendall(request.serialize())
                database_response = ResponseObject()
                database_raw = database_socket.recv(1024)
                print(f"Login Process {os.getpid()} recieved from database: {database_raw}")
                if not database_raw:
                    print("Connection closed by the server.")
                    break
                status, remaining = database_response.deserialize(database_raw)
                if status != Status.SUCCESS:
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
                    database_socket.sendall(request.serialize())
                    database_response = ResponseObject()
                    try:
                        database_raw = database_socket.recv(1024)
                        if not database_raw:
                            print("Connection closed by the server.")
                            break
                        status, remaining = database_response.deserialize(database_raw)
                        if status != Status.SUCCESS:
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
                    database_socket.sendall(request.serialize())
                    database_response = ResponseObject()
                    try:
                        database_raw = database_socket.recv(1024)
                        if not database_raw:
                            print("Connection closed by the server.")
                            break
                        status, remaining = database_response.deserialize(database_raw)
                        if status != Status.SUCCESS:
                            print("Parsing Failed")
                            break
                        print(f"Login Process {os.getpid()} recieved from database: {database_raw}")
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

    # Set up the database process, and wait for it to start
    database_start =  mp.Event()
    database = mp.Process(target=database_process, args=(host, database_port, database_start,))
    database.start()
    database_start.wait()

    # Set up socket to listen for connection requests
    connect_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
