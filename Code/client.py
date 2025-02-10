import socket
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext

class LoginClient:
    def __init__(self, server_socket):
        self.window = tk.Tk()
        self.server_socket = server_socket
        self.window.title("Login")
        self.create_login_ui()
        self.window.mainloop()
    
    def create_login_ui(self):
        """Create the login UI"""
        self.username_label = tk.Label(self.window, text="Username:")
        self.username_label.pack()
        self.username_entry = tk.Entry(self.window)
        self.username_entry.pack()
        self.username_button = tk.Button(self.window, text="Submit Username", command=self.send_username)
        self.username_button.pack()

        self.password_label = tk.Label(self.window, text="Password:")
        self.password_entry = tk.Entry(self.window)
        self.password_button = tk.Button(self.window, text="Submit Password", command=self.send_password)
    
    def send_username(self):
        """Send username to server"""
        username = self.username_entry.get()
        if not username:
            messagebox.showwarning("Input Error", "Username cannot be empty!")
            return

        message = ("username " + username).encode("utf-8")
        self.server_socket.sendall(message)
        response = self.server_socket.recv(1024)
        if not response:
            messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
            self.window.destroy()
            return
        response = response.decode("utf-8")
        print(f"Received {response}")

        if response == "Enter Password":
            self.username_entry.config(state=tk.DISABLED)
            self.username_button.config(state=tk.DISABLED)
            self.password_label.pack()
            self.password_entry.pack()
            self.password_button.pack()
        elif response == "No User":
            messagebox.showerror("Login Failed", "No such username exists! Please register for an account.")
            self.window.destroy()
            RegisterClient(server_socket)
        else:
            messagebox.showerror("Error", "Unexpected server response.")

    def send_password(self):
        """Send password to server"""
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Input Error", "Password cannot be empty!")
            return

        message = ("password " + password).encode("utf-8")
        self.server_socket.sendall(message)
        response = self.server_socket.recv(1024)
        if not response:
            messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
            self.window.destroy()
            return
        response = response.decode("utf-8")
        print(f"Received {response}")

        if response == "Logged In":
            messagebox.showinfo("Success", "Login Successful!")
            self.window.destroy()
            # ChatWindow(self.server_socket)  # Open chat window
        elif response == "Wrong Password":
            messagebox.showerror("Login Failed", "Wrong password!")
        else:
            messagebox.showerror("Error", "Unexpected server response.")


class RegisterClient:
    def __init__(self, server_socket):
        self.window = tk.Tk()
        self.server_socket = server_socket
        self.window.title("Register")
        self.create_register_ui()
        self.window.mainloop()

    def create_register_ui(self):
        """Create the register UI"""
        self.username_label = tk.Label(self.window, text="Username:")
        self.username_label.pack()
        self.username_entry = tk.Entry(self.window)
        self.username_entry.pack()

        self.password_label = tk.Label(self.window, text="Password:")
        self.password_label.pack()
        self.password_entry = tk.Entry(self.window)
        self.password_entry.pack()

        self.confirm_password_label = tk.Label(self.window, text="Confirm Password")
        self.confirm_password_label.pack()
        self.confirm_password_entry = tk.Entry(self.window)
        self.confirm_password_entry.pack()

        self.confirm_password_button = tk.Button(self.window, text="Register", command=self.send_new_user)
        self.confirm_password_button.pack()

    def send_new_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not username:
            messagebox.showwarning("Input Error", "Username cannot be empty!")
            return
        if not password or not confirm_password:
            messagebox.showwarning("Input Error", "Password cannot be empty!")
            return
        if password != confirm_password:
            messagebox.showwarning("Input Error", "Passwords must match!")
            return

        message = ("add " + username + " " + password).encode("utf-8")
        self.server_socket.sendall(message)
        response = self.server_socket.recv(1024)
        if not response:
            messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
            self.window.destroy()
            return
        response = response.decode("utf-8")
        print(f"Received {response}")

        if response == "Success":
            messagebox.showinfo("Success", "Registration Successful!")
            self.window.destroy()
            LoginClient(server_socket)
        elif response == "Exists":
            messagebox.showwarning("Error", "Username already exists.")
            return
        elif response == "Fail":
            messagebox.showerror("Server Error", "Failed to create new user. Please try again.")
        else:
           messagebox.showerror("Error", "Unexpected server response.") 

class ChatClient:
    pass

# run python client.py HOSTNAME PORTNAME

def client_user(server_socket, username):
    data = server_socket.recv(1024)
    data = data.decode("utf-8")
    if data == "Logged In":
        print("Logged In")
    elif data == "Duplicate":
        print("Already Logged In Elsewhere")
        return
    else:
        print("Login Failed")
        return
    while True:
        message = input(f"Enter a message as User {username}: ")
        if message == "exit":
            break
        message = message.encode("utf-8")
        server_socket.sendall(message)
        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data = data.decode("utf-8")
        print(f"Received: {data}")

def client_create_user(server_socket):
    username = ""
    while True:
        print("Create New User:")
        username = input("Enter Username: ")
        password = input("Enter Password: ")
        confirm_password = input("Confirm Password: ")
        if password == confirm_password:
            message = ("add " + username + " " + password).encode("utf-8")
            server_socket.sendall(message)

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data = data.decode("utf-8")
        print(f"Recieved {data}")
        if data == "Success":
            print(f"Created User with Username: {username}, Password: {password}")
            return
        elif data == "Exists":
            print("User Exists.")
            return
        elif data == "Fail":
            print("Failed to create new user. Try again.")
        else:
            print("Error")

def client_login(server_socket):
    username = ""
    while True:
        print("Login:")
        username = input("Enter Username: ")
        message = ("username " + username).encode("utf-8")
        server_socket.sendall(message)

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data = data.decode("utf-8")
        print(f"Recieved {data}")
        if data == "Enter Password":
            break
        elif data == "No User":
            print("No such username exists")
            client_create_user(server_socket)
        else:
            print("Error")
    
    password = ""
    while True:
        password = input("Enter Password: ")
        message = ("password " + password).encode("utf-8")
        server_socket.sendall(message)

        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data = data.decode("utf-8")
        print(f"Recieved {data}")
        if data == "Logged In":
            print("Logging In")
            client_user(server_socket, username)
            break
        elif data == "Wrong Password":
            print("Wrong Password")
        else:
            print("Error")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py HOSTNAME PORTNAME")
        exit(1)
    host, port = sys.argv[1], int(sys.argv[2])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, int(port)))

    LoginClient(server_socket)
