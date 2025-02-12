#!/usr/bin/env python3
import os
import socket
import sys
import multiprocessing as mp
import selectors

from Modules.DatabaseManager import DatabaseManager
from Modules.DataObjects import DataObject, MessageObject
from Modules.SelectorData import SelectorData
from Modules.Flags import Request, Status

def database_request_handler(db : DatabaseManager, 
                             request : DataObject, 
                             key : selectors.SelectorKey, 
                             online_username : dict[str, selectors.SelectorKey], 
                             online_address : dict[str, str]) -> DataObject:
    address_string = f"{key.data.address}"
    if request.request == Request.CONFIRM_LOGIN:
        if request.user == "":
            request.update(status=Status.ERROR)
        elif request.user in online_username:
            request.update(status=Status.MATCH)
        else:
            online_username[request.user] = key
            online_address[address_string] = request.user
            request = db.handler(request)
    elif request.request == Request.GET_ONLINE_USERS:
        user_list = list(online_username.keys())
        request.update(status=Status.SUCCESS, datalen=len(user_list), data=user_list)
    elif request.request == Request.SEND_MESSAGE:
        message_raw = request.data[0]
        message = MessageObject(method="serial", serial = message_raw.encode("utf-8"))
        print(f"Database Processing Message: {message.to_string()}")
        
        request = db.handler(request)
        print(request.to_string())
        if request.status == Status.SUCCESS and message.recipient in online_username:
            target_key = online_username[message.recipient]
            request.update(request=Request.ALERT_MESSAGE, status=Status.PENDING)
            target_key.data.outbound.put(request.serialize())
            request.update(request=Request.SEND_MESSAGE, status=Status.SUCCESS)
    else:
        request = db.handler(request)
        print(f"Handler Responds with {request.to_string()}")
    return request

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
                            key.data.inbound += recieve
                            serial, key.data.inbound = DataObject.get_one(key.data.inbound)
                            print(serial, key.data.inbound)
                            if serial != b"":
                                request = DataObject(method="serial", serial=serial)
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
        request = DataObject(request=Request.CONFIRM_LOGIN, user=username)
        keys["database"].fileobj.sendall(request.serialize())
    except Exception as e:
        print(f"Error in User process {os.getpid()} when sending Login to database:", e)
        user_selector.close()
        return

    # Wait for confirmation of Login (Ignore all other communications until the login is confirmed)
    logged_in = False
    try:
        while not logged_in:
            events = user_selector.select(timeout=None)
            for key, mask in events:
                source = key.data.source
                if source == "database" and mask & selectors.EVENT_READ:
                    database_raw = keys["database"].fileobj.recv(1024)
                    if not database_raw:
                        raise Exception(f"Connection Closed By {source}")
                    keys["database"].data.inbound += database_raw
                    serial, keys["database"].data.inbound = DataObject.get_one(keys["database"].data.inbound)
                    print(serial, keys["database"].data.inbound)
                    if serial != b"":
                        database_response = DataObject(method="serial", serial=serial)
                        print(f"User Process {os.getpid()} recieved {database_response.to_string()}")
                        if database_response.request != Request.CONFIRM_LOGIN:
                            continue
                        if database_response.status == Status.SUCCESS:
                            logged_in = True
                        keys["client"].fileobj.sendall(database_response.serialize())
                        if not logged_in:
                            raise Exception("Not Logged In")                
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
                        keys["client"].data.inbound += raw_client
                        serial, keys["client"].data.inbound = DataObject.get_one(keys["client"].data.inbound)
                        if serial != b"":
                            client_request = DataObject(method="serial", serial=serial)
                            # Standard Commands can be passed directly to the database process
                            if client_request.request in [Request.GET_ONLINE_USERS, Request.SEND_MESSAGE, Request.GET_USERS, 
                                                          Request.DELETE_USER, Request.GET_MESSAGE, Request.DELETE_MESSAGE, 
                                                          Request.CONFIRM_READ]:
                                keys["database"].data.outbound.put(client_request.serialize())
                                print(f"{keys['database'].data.outbound.empty()} Outgoing to {source}: {client_request.to_string()}")
                            elif client_request.request == Request.CONFIRM_LOGOUT:
                                client_request.update(status=Status.SUCCESS)
                                keys["client"].data.outbound.put(client_request.serialize())
                                print(f"{keys['client'].data.outbound.empty()} Outgoing to Client: {client_request.to_string()}")
                            elif client_request.request == Request.ALERT_MESSAGE:
                                client_request.update(status=Status.SUCCESS)
                                keys["client"].data.outbound.put(client_request.serialize())
                                print(f"{keys['client'].data.outbound.empty()} Outgoing to Client: {client_request.to_string()}")
                            elif client_request.request in [Request.CHECK_USERNAME, Request.CHECK_PASSWORD, Request.CONFIRM_LOGIN]:
                                raise Exception("Unexpected Communication Flag")
                            else:
                                raise Exception("Unhandled Communication Flag")
                    if mask & selectors.EVENT_WRITE and not key.data.outbound.empty():
                        message = key.data.outbound.get()
                        key.fileobj.sendall(message)
                if source == "database":
                    if mask & selectors.EVENT_READ:
                        database_raw = keys["database"].fileobj.recv(1024)
                        if not database_raw:
                            raise Exception("Connection Closed By Server")
                        keys["database"].data.inbound += database_raw
                        serial, keys["database"].data.inbound = DataObject.get_one(keys["database"].data.inbound)
                        if serial != b"":
                            database_response = DataObject(method="serial", serial=serial)
                            print(f"User Process {os.getpid()} recieved {database_response.to_string()}")
                            if database_response.request in [Request.GET_ONLINE_USERS, Request.SEND_MESSAGE, Request.ALERT_MESSAGE, 
                                                             Request.GET_USERS, Request.GET_MESSAGE, Request.DELETE_MESSAGE,
                                                             Request.CONFIRM_READ]:
                                keys["client"].data.outbound.put(database_response.serialize())
                                print(f"{keys['client'].data.outbound.empty()} Outgoing to {source}: {database_response.to_string()}")
                            elif database_response.request == Request.DELETE_USER:
                                keys["client"].data.outbound.put(database_response.serialize())
                                print(f"{keys['client'].data.outbound.empty()} Outgoing to {source}: {database_response.to_string()}")
                                break
                            elif client_request.request in [Request.CHECK_USERNAME, Request.CHECK_PASSWORD, Request.CONFIRM_LOGIN]:
                                raise Exception("Unexpected Communication Flag")
                            else:
                                raise Exception("Unhandled Communication Flag")
                    if mask & selectors.EVENT_WRITE and not key.data.outbound.empty():
                        message = key.data.outbound.get()
                        key.fileobj.sendall(message)
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

    client_buffer = b""
    database_buffer = b""

    try:
        print(f"Login process {os.getpid()} handling connection from {address}")
        password_confirmed = False
        while not password_confirmed:
            data = client_connection.recv(1024)
            # Check if connection closed by client
            if not data:
                raise Exception("Connection closed by the server.")
            client_buffer += data
            serial, client_buffer = DataObject.get_one(client_buffer)
            print(serial, client_buffer)
            if serial != b"":
                user_request = DataObject(method="serial", serial=serial)
                print(f"Login process {os.getpid()} got data {user_request.to_string()}")
                if user_request.request == Request.CHECK_USERNAME:
                    request = user_request
                    database_socket.sendall(request.serialize())
                    database_responded = False
                    database_buffer = b""
                    while not database_responded:
                        database_raw = database_socket.recv(1024)
                        if not database_raw:
                            raise Exception("Connection closed by the database.")
                        database_buffer += database_raw
                        serial, database_buffer = DataObject.get_one(database_buffer)
                        if serial != b"":
                            database_responded = True
                            database_response = DataObject(method="serial", serial=serial)
                            print(f"Login Process {os.getpid()} recieved from database: {database_response.to_string()}")
                            if database_response.status == Status.MATCH and database_response.data[0] == user_request.data[0]:
                                username = database_response.data[0]
                            user_request = database_response
                elif user_request.request == Request.CHECK_PASSWORD:
                    if not username:
                        user_request.update(status=Status.ERROR)
                    else:
                        request = user_request
                        database_socket.sendall(request.serialize())

                        database_responded = False
                        database_buffer = b""
                        while not database_responded:
                            database_raw = database_socket.recv(1024)
                            if not database_raw:
                                raise Exception("Connection closed by the database.")
                            database_buffer += database_raw
                            serial, database_buffer = DataObject.get_one(database_buffer)
                            if serial != b"":
                                database_responded = True
                                database_response = DataObject(method="serial", serial=serial)
                                print(f"Login Process {os.getpid()} recieved from database: {database_response.to_string()}")
                                user_request = database_response
                                if database_response.status == Status.MATCH:
                                    user_start =  mp.Event()
                                    client_user = mp.Process(target=user_process, args=(client_connection, address, database, user_start, username))
                                    client_user.start()
                                    user_start.wait()
                                    password_confirmed = True
                elif user_request.request == Request.CREATE_USER:
                    if not user_request.data[0] or not user_request.data[1]:
                        user_request.update(status=Status.ERROR)
                    else:
                        request = user_request
                        database_socket.sendall(request.serialize())

                        request = user_request
                        database_responded = False
                        database_buffer = b""
                        while not database_responded:
                            database_raw = database_socket.recv(1024)
                            if not database_raw:
                                raise Exception("Connection closed by the server.")
                            database_buffer += database_raw
                            serial, database_buffer = DataObject.get_one(database_buffer)
                            if serial != b"":
                                database_responded = True
                                database_response = DataObject(method="serial", serial=serial)
                                user_request = database_response
                print(f"Login Process {os.getpid()} sends: {user_request.to_string()}")
                client_connection.sendall(user_request.serialize())
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
