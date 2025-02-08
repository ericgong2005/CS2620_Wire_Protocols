import socket
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext

class ChatClient:
    def __init__(self, root, server_socket):
        self.root = root
        self.server_socket = server_socket
        self.root.title("Chat Login")
        self.create_login_ui()
        self.root.mainloop()

    def create_login_ui(self):
        """Create the login UI."""
        self.username_label = tk.Label(self.root, text="Username:")
        self.username_label.pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()
        self.username_button = tk.Button(self.root, text="Submit Username", command=self.send_username)
        self.username_button.pack()

        self.password_label = tk.Label(self.root, text="Password:")
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_button = tk.Button(self.root, text="Submit Password", command=self.send_password)

    def send_username(self):
        """Send the username to the server."""
        username = self.username_entry.get()
        if not username:
            messagebox.showwarning("Input Error", "Username cannot be empty!")
            return
        
        message = ("username " + username).encode("utf-8")
        self.server_socket.sendall(message)
        response = self.server_socket.recv(1024).decode("utf-8")

        if response == "Enter Password":
            self.username_entry.config(state=tk.DISABLED)
            self.username_button.config(state=tk.DISABLED)
            self.password_label.pack()
            self.password_entry.pack()
            self.password_button.pack()
        elif response == "No User":
            messagebox.showerror("Login Failed", "No such username exists!")
        else:
            messagebox.showerror("Error", "Unexpected server response.")

    def send_password(self):
        """Send the password to the server."""
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Input Error", "Password cannot be empty!")
            return

        message = ("password " + password).encode("utf-8")
        self.server_socket.sendall(message)
        response = self.server_socket.recv(1024).decode("utf-8")

        if response == "Logged In":
            messagebox.showinfo("Success", "Login Successful!")
            self.root.destroy()
            ChatWindow(self.server_socket)  # Open chat window
        elif response == "Wrong Password":
            messagebox.showerror("Login Failed", "Wrong password!")
        else:
            messagebox.showerror("Error", "Unexpected server response.")

class ChatWindow:
    def __init__(self, server_socket):
        self.server_socket = server_socket
        self.window = tk.Tk()
        self.window.title("Chat Room")
        
        self.chat_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state=tk.DISABLED, height=15, width=50)
        self.chat_area.pack(pady=10)
        
        self.message_entry = tk.Entry(self.window, width=40)
        self.message_entry.pack(pady=5, side=tk.LEFT)
        self.send_button = tk.Button(self.window, text="Send", command=self.send_message)
        self.send_button.pack(pady=5, side=tk.RIGHT)
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_connection)
        self.window.mainloop()

    def send_message(self):
        message = self.message_entry.get()
        if message == "exit":
            self.close_connection()
            return

        if message:
            self.server_socket.sendall(message.encode("utf-8"))
            self.display_message(f"You: {message}")
            self.message_entry.delete(0, tk.END)
            
            data = self.server_socket.recv(1024).decode("utf-8")
            self.display_message(f"Server: {data}")

    def display_message(self, message):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def close_connection(self):
        self.server_socket.close()
        self.window.destroy()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py HOSTNAME PORTNAME")
        exit(1)
    host, port = sys.argv[1], int(sys.argv[2])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, port))
    
    root = tk.Tk()
    ChatClient(root, server_socket)