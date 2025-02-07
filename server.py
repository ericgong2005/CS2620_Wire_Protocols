#!/usr/bin/env python3
import os
import socket
import sys

# Tools

def convert_word(word):
    vowels = "aeiou"
    if word[0].lower() in vowels:
        return word + "yay"
    else:
        for i, letter in enumerate(word):
            if letter.lower() in vowels:
                return word[i:] + word[:i] + "ay"
        return word + "ay"  # In case there are no vowels

def trans_to_pig_latin(words):
    pig_latin_words = [convert_word(word) for word in words]
    return " ".join(pig_latin_words)

# Handle the client
def client(connection, address):
    """Handle client connection: receive commands and send responses."""
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
            if words[0] == "count":
                # Count the remaining words.
                response = str(len(words) - 1)
            elif words[0] == "translate":
                response = trans_to_pig_latin(words[1:])
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
                client(client_connection, addr)
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
