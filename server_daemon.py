#!/usr/bin/env python3
import os
import socket
import sys
from pathlib import Path
import csv

PASSWORD_FILE = Path(__file__).parent / "User_Data/passwords.csv"

# Tools
'''
traverse_passwords checks for the existence of a username or a username-password pair
Will return an int flag:
-1: username not found
0 : username found, but password does not match
1 : username/password both match
'''
def traverse_passwords(username : str, password: str) -> int:
    with open(PASSWORD_FILE, mode='r', newline='') as file:
        csv_data = csv.reader(file)
        for row in csv_data:
            if row[0] == username:
                return (1 if row[1] == password else 0)

# Handle the client
def login_process(connection, address):
    """Handle client connection: receive commands and send responses."""
    username = ""
    try:
        print(f"Child {os.getpid()} handling connection from {address}")
        while True:
            data = connection.recv(1024)
            print(f"Child {os.getpid()} got data {data}")
            if not data:
                break  # Connection closed by client
            words = data.decode("utf-8").split()
            if not words:
                continue  # Skip if no data
            elif words[0] == "username":
                if traverse_passwords(words[1], None) != -1 :
                    username = words[1]
                    response = f"Enter password for {username}"
                else:
                    response = "No such user"
            elif words[0] == "password":
                if not username:
                    response = "enter username"
                else:
                    if traverse_passwords(username, words[1]) == 1:
                        response = "logged in"
                    else:
                        response = f"Wrong password for {username}"
            else:
                response = "Unknown command"
            connection.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in child {os.getpid()}:", e)
    finally:
        connection.close()
        print(f"Child {os.getpid()} closing connection from {address}")
        os._exit(0)

def main(host : str, port : int):
    connect_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_request.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connect_request.bind((host, port))
    connect_request.listen(5)
    print(f"Daemon listening on {(host, port)}")

    while True:
        try:
            client_connection, addr = connect_request.accept()
            # Fork a child process to handle client connections
            pid = os.fork()
            if pid == 0: # Child
                connect_request.close()  # Close listening socket
                login_process(client_connection, addr)
            else: # Parent
                client_connection.close()  # Close the client socket
                try:
                    while True:
                        # Wait for any child process that has terminated.
                        finished_pid, _ = os.waitpid(-1, os.WNOHANG)
                        if finished_pid == 0:
                            break
                except ChildProcessError:
                    pass
        except KeyboardInterrupt:
            print("Daemon shutting down (KeyboardInterrupt)")
            break
        except Exception as e:
            print("Error accepting connections:", e)

    connect_request.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py HOSTNAME PORTNAME")
        sys.exit(1)
    main(sys.argv[1], int(sys.argv[2]))
