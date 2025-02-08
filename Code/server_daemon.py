#!/usr/bin/env python3
import os
import socket
import sys
from pathlib import Path
import multiprocessing as mp

from Modules.database_manager import DatabaseManager, QueryObject
from Modules.constants import DB, Status

PASSWORD_FILE = Path(__file__).parent / "User_Data/passwords.csv"

def database_proccess(database_queue, host, database_port):
    """
    Handle all requests to the database
    """

    print(f"Database process {os.getpid()} started")

    db = DatabaseManager()

    # Add some fake users in case the db is empty
    db.insert_user("a", "b")
    db.insert_user("abcd", "1234")

    online = {}

    while True:
        request = database_queue.get()
        print(f"Database recieved Request {request.to_string()}")
        if request.request == DB.LOGIN:
            if request.username in online:
                request.pipe.send(Status.DUPLICATE)
            else:
                online[request.username] = (request.pid, request.pipe)
                request.pipe.send(Status.SUCCESS)
        elif request.request == DB.LOGOUT:
            if request.username in online:
                del online[request.username]
        elif request.request == DB.CURRENT_USERS:
            request.pipe.send((Status.SUCCESS, list(online.keys())))
        elif request.request == DB.NOTIFY:
            target = request.data[0]
            if target in online:
                request.pipe.send((Status.SUCCESS, None))
            else:
                request.pipe.send((Status.FAIL, None))
        else:
            try:
                request.pipe.send(db.handler(request)) 
                print(f"Database answered {request.to_string()}")
            except Exception as e:
                del online[request.username]
                print("Database failed to answer request due to", e)

def user_process(connection, address, database_queue, user_start, username) :
    """
    Handle client connection normal user activity
    """
    user_start.set()
    user_end, database_end = mp.Pipe()
    logged_in = False
    try:
        print(f"User process {os.getpid()} handling connection from {address}")

        request = QueryObject(DB.LOGIN, username, None, database_end, os.getpid())
        database_queue.put(request)
        status = user_end.recv()
        print(f"User Process {os.getpid()} recieved {status}")
        if status == Status.SUCCESS:
            logged_in = True
            response = "Logged In"
        elif status == Status.DUPLICATE:
            response = "Duplicate"
        else:
            response = "Failed"
        
        connection.sendall(response.encode("utf-8"))

        while logged_in:
            data = connection.recv(1024)
            print(f"User process {os.getpid()} got data {data}")

            # Check if connection closed by client
            if not data:
                break  

            words = data.decode("utf-8").split()
            if words[0] == "get":
                request = QueryObject(DB.CURRENT_USERS, username, None, database_end, os.getpid())
                database_queue.put(request)
                status, users = user_end.recv()
                if(status == Status.SUCCESS):
                    response = f"Users: {users}"
                else:
                    response = "Failed to Retrieve Active Users"
            elif words[0] == "ping":
                request = QueryObject(DB.NOTIFY, username, [words[1]], database_end, os.getpid())
                database_queue.put(request)
                status, users = user_end.recv()
                if(status == Status.SUCCESS):
                    response = "Ping Sent"
                else:
                    response = "Failed to Send Ping"
            else:
                response = f"Success: {data}"

            connection.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in User process {os.getpid()}:", e)
    finally:
        if logged_in:
            request = QueryObject(DB.LOGOUT, username, None, None, os.getpid())
            database_queue.put(request)
        connection.close()
        user_end.close() 
        database_end.close()
        print(f"User process {os.getpid()} closing connection from {address}")

def login_process(connection, address, database_queue):
    """
    Handle client connection login
    """

    username = ""
    login_end, database_end = mp.Pipe()

    try:
        print(f"Login process {os.getpid()} handling connection from {address}")

        while True:
            data = connection.recv(1024)
            print(f"Login process {os.getpid()} got data {data}")

            # Check if connection closed by client
            if not data:
                break  

            words = data.decode("utf-8").split()
            if not words:
                continue
            elif words[0] == "username":
                request = QueryObject(DB.CHECK_USERNAME, None, [words[1]], database_end, os.getpid())
                database_queue.put(request)
                try:
                    status, result = login_end.recv()
                    print(f"Login Process {os.getpid()} recieved {status} {result}")
                except Exception as e:
                    print("User process failed to receive response from database due to", e)
                    break
                if status == Status.SUCCESS and result == words[1]:
                    username = result
                    response = "Enter Password"
                else:
                    response = "No User"
            elif words[0] == "password":
                if not username:
                    response = "Enter Username"
                else:
                    request = QueryObject(DB.CHECK_PASSWORD, None, [username, words[1]], database_end, os.getpid())
                    database_queue.put(request)
                    try:
                        status, result = login_end.recv()
                        print(f"Login Process {os.getpid()} recieved {status} {result}")
                    except Exception as e:
                        print("User process failed to receive response from database due to", e)
                        break
                    if status == Status.SUCCESS and result == username:
                        user_start =  mp.Event()
                        client_user = mp.Process(target=user_process, args=(connection, address, database_queue, user_start, username))
                        client_user.start()
                        user_start.wait()
                        response = "Logged In"
                        connection.sendall(response.encode("utf-8"))
                        break
                    else:
                        response = "Wrong Password"
            elif words[0] == "add":
                if not words[1] or not words[2]:
                    response = "Fail"
                else:
                    request = QueryObject(DB.ADD_USER, None, [words[1], words[2]], database_end, os.getpid())
                    database_queue.put(request)
                    try:
                        status, _result = login_end.recv()
                        print(f"Login Process {os.getpid()} recieved {status} {result}")
                    except Exception as e:
                        print("User process failed to receive response from database due to", e)
                        break
                    if status == Status.SUCCESS:
                        response = "Success"
                    elif status == Status.DUPLICATE:
                        response = "Exists"
                    else:
                        response = "Fail"          
            connection.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in login process {os.getpid()}:", e)
    finally:
        connection.close()
        login_end.close() 
        database_end.close()
        print(f"Login process {os.getpid()} closing connection from {address}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python server.py HOSTNAME DAEMON_PORTNAME DATABASE_PORTNAME")
        sys.exit(1)
    host, daemon_port, database_port = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

    # Set the child creation type to spawn to support windows
    mp.set_start_method('spawn')

    # Set up the database process
    database_queue = mp.Queue()
    database_process = mp.Process(target=database_proccess, args=(database_queue, host, database_port))
    database_process.start()

    # Set up socket to listen for connection requests
    connect_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_request.bind((host, daemon_port))
    connect_request.listen(5)
    print(f"Daemon listening on {(host, daemon_port)}")

    while True:
        try:
            client_connection, address = connect_request.accept()

            # Fork a child process to handle client login
            client_login = mp.Process(target=login_process, args=(client_connection, address, database_queue))
            client_login.start()

            # Close client connection on daemon end
            client_connection.close()
        except KeyboardInterrupt:
            print("Shutting Down: KeyboardInterrupt")
            break
        except Exception as e:
            print("Error:", e)
    
    connect_request.close()
