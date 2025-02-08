#!/usr/bin/env python3
import os
import socket
import sys
from pathlib import Path
import csv
import multiprocessing as mp

PASSWORD_FILE = Path(__file__).parent / "User_Data/passwords.csv"

def user_process(connection, address, user_start) :
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

def traverse_passwords(username : str, password: str) -> int:
    """
    traverse_passwords checks for the existence of a username or a username-password pair
    Will return an int flag:
    -1: username not found
    0 : username found, but password does not match
    1 : username/password both match
    """
    with open(PASSWORD_FILE, mode='r', newline='') as file:
        csv_data = csv.reader(file)
        for row in csv_data:
            if row[0] == username:
                return (1 if row[1] == password else 0)
    return -1

def login_process(connection, address):
    """
    Handle client connection login
    """
    username = ""
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
                if traverse_passwords(words[1], None) != -1 :
                    username = words[1]
                    response = "Enter Password"
                else:
                    response = "No User"
            elif words[0] == "password":
                if not username:
                    response = "Enter Username"
                else:
                    if traverse_passwords(username, words[1]) == 1:
                        user_start =  mp.Event()
                        client_user = mp.Process(target=user_process, args=(connection, address, user_start))
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
            client_login = mp.Process(target=login_process, args=(client_connection, address,))
            client_login.start()

            # Close client connection on daemon end
            client_connection.close()
        except KeyboardInterrupt:
            print("Shutting Down: KeyboardInterrupt")
            break
        except Exception as e:
            print("Error:", e)
    
    connect_request.close()
