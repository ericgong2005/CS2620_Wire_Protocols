#!/usr/bin/env python3
import os
import socket
import sys

# --- Pig Latin conversion functions ---

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

# --- Client handler function ---

def handle_client(conn, addr):
    """Handle client connection: receive commands and send responses."""
    try:
        print(f"Child {os.getpid()} handling connection from {addr}")
        while True:
            data = conn.recv(1024)
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
            conn.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Error in child {os.getpid()}:", e)
    finally:
        conn.close()
        print(f"Child {os.getpid()} closing connection from {addr}")
        # Ensure the child process exits.
        os._exit(0)

def main(host, port):

    # Create the listening socket.
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind((host, port))
    lsock.listen(5)
    print(f"Daemon listening on {(host, port)}")

    while True:
        try:
            conn, addr = lsock.accept()
            # Fork a child process to handle this connection.
            pid = os.fork()
            if pid == 0:
                # In the child process.
                lsock.close()  # Close listening socket inherited from parent.
                handle_client(conn, addr)
            else:
                # In the parent process.
                conn.close()  # Close the connected socket (child handles it).
                # Optionally, reap any zombie children.
                try:
                    while True:
                        # Wait for any child process that has terminated.
                        finished_pid, _ = os.waitpid(-1, os.WNOHANG)
                        if finished_pid == 0:
                            break  # No more zombies.
                except ChildProcessError:
                    # No child processes.
                    pass
        except KeyboardInterrupt:
            print("Daemon shutting down (KeyboardInterrupt)")
            break
        except Exception as e:
            print("Error accepting connections:", e)

    lsock.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py HOST PORT")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    main(host, port)
