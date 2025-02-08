#!/usr/bin/env python3
import os
import socket
import sys
from pathlib import Path
import multiprocessing as mp

from Modules.database_manager import DatabaseManager
from Modules.constants import DB, Status

PASSWORD_FILE = Path(__file__).parent / "User_Data/passwords.csv"

def database_proccess(database_queue):
    """
    Handle all requests to the database
    """

    print(f"Database process {os.getpid()} started")

    db = DatabaseManager()

    # Add some fake users in case the db is empty
    db.insert_user("a", "b")
    db.insert_user("abcd", "1234")

    while True:
        request = database_queue.get()
        print(f"Database recieved Request {request}")
        if request["type"] == DB.GET_PASSWORD:
            request["return"].send(db.get_password(request["data"]))
        else:
            request["return"].send((Status.INVALID_INPUT, None))   
        request["return"].close()

def user_process(connection, address, database_queue, user_start, username) :
    """
    Handle client connection normal user activity
    """
    user_start.set()
    try:
        print(f"User process {os.getpid()} handling connection from {address}")
        while True:
            data = connection.recv(1024)
            print(f"User process {os.getpid()} got data {data}")

            # Check if connection closed by client
            if not data:
                break  

            data = data.decode("utf-8")
            
            response = f"Success: {data}"

            connection.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in User process {os.getpid()}:", e)
    finally:
        connection.close()
        print(f"User process {os.getpid()} closing connection from {address}")

def login_process(connection, address, database_queue):
    """
    Handle client connection login
    """

    username = ""
    password = ""
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
                login_end, database_end = mp.Pipe()
                request = {"type" : DB.GET_PASSWORD, "data": words[1], "return" : database_end}
                database_queue.put(request)
                status, result = login_end.recv()
                print(f"Login Process Recieved {status} {result}")
                if status == Status.SUCCESS:
                    username = words[1]
                    password = result
                    response = "Enter Password"
                else:
                    response = "No User"
                login_end.close()
            elif words[0] == "password":
                if not username:
                    response = "Enter Username"
                else:
                    if password == words[1]:
                        user_start =  mp.Event()
                        client_user = mp.Process(target=user_process, args=(connection, address, database_queue, user_start, username))
                        client_user.start()
                        user_start.wait()
                        response = "Logged In"
                        connection.sendall(response.encode("utf-8"))
                        break
                    else:
                        response = f"Wrong Password"
            else:
                response = "Error"
            connection.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in login process {os.getpid()}:", e)
    finally:
        connection.close()
        print(f"Login process {os.getpid()} closing connection from {address}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py HOSTNAME PORTNAME")
        sys.exit(1)
    host, port = sys.argv[1], int(sys.argv[2])

    # Set the child creation type to spawn to support windows
    mp.set_start_method('spawn')

    # Set up the database process
    database_queue = mp.Queue()
    database_process = mp.Process(target=database_proccess, args=(database_queue,))
    database_process.start()

    # Set up socket to listen for connection requests
    connect_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_request.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connect_request.bind((host, port))
    connect_request.listen(5)
    print(f"Daemon listening on {(host, port)}")

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
