#!/usr/bin/env python3
import os
import socket
import sys
from pathlib import Path
import csv

PASSWORD_FILE = Path(__file__).parent / "User_Data/passwords.csv"

# Tools
'''
Given an inputted username, if the username exists, return [True, password_hash]
Otherwise, return [False, None]
'''
def traverse_passwords(command: str, username : str, password: str) -> tuple[bool, str]:
    data = []
    with open(PASSWORD_FILE, mode='r', newline='') as file:
        csv_data = csv.reader(file)
        for row in csv_data:
            data.append(row)

    for row in data:
        if row[0] == username:
            if command == "username":
                return (True, row[1])
            else:
                return (password == row[1], username)
    return False, None   

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
                exists, _password = traverse_passwords("username", words[1], None)
                if exists:
                    username = words[1]
                    response = "Enter password"
                else:
                    response = "No such user"
            elif words[0] == "password":
                if not username:
                    response = "enter username"
                else:
                    correct, username = traverse_passwords("password", username, words[1])
                    if correct:
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

def main(host, port):

    # Create the listening socket.
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((host, port))
    listen_socket.listen(5)
    print(f"Daemon listening on {(host, port)}")

    while True:
        try:
            client_connection, addr = listen_socket.accept()
            # Fork a child process to handle client connections
            pid = os.fork()
            if pid == 0: # Child
                listen_socket.close()  # Close listening socket
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

    listen_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py HOST PORT")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    main(host, port)
