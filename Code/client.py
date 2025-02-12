import socket
import sys
import selectors
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext

from Modules.Flags import Request, Status
from Modules.DataObjects import DataObject, MessageObject
from Modules.selector_data import SelectorData

# run python client.py HOSTNAME PORTNAME

class LoginClient:
    def __init__(self, server_socket):
        self.window = tk.Tk()
        self.window.geometry("500x200")
        self.server_socket = server_socket
        self.window.title("Login")
        self.create_login_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.close_connection)
        self.window.mainloop()
    
    def create_login_ui(self):
        """Create the login UI"""
        self.username_label = tk.Label(self.window, text="Username:")
        self.username_label.grid(row=0, column=0, pady=5, padx=2)
        self.username_entry = tk.Entry(self.window)
        self.username_entry.grid(row=0, column=1, pady=5, padx=2) 
        self.username_button = tk.Button(self.window, text="Submit Username", command=self.send_username)
        self.username_button.grid(row=0, column=2, pady=5, padx=2)

        self.password_label = tk.Label(self.window, text="Password:")
        self.password_entry = tk.Entry(self.window, show="*")
        self.password_button = tk.Button(self.window, text="Submit Password", command=self.send_password)

        self.window.update_idletasks()
    
    def send_username(self):
        """Send username to server"""
        username = self.username_entry.get()
        if not username:
            messagebox.showwarning("Input Error", "Username cannot be empty!")
            return
        
        request = DataObject(request=Request.CHECK_USERNAME, datalen=1, data=[username])
        print(f"Sending: {request.to_string()}")
        self.server_socket.sendall(request.serialize())
        data_buffer = b""
        received = False
        while not received:
            data = self.server_socket.recv(1024)
            if not data:
                messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
                self.close_connection()
                return
            data_buffer += data
            serial, data_buffer = DataObject.get_one(data_buffer)
            if serial != b"":
                received = True
                response = DataObject(method="serial", serial=serial)
                print(f"Received: {response.to_string()}")
                if response.status == Status.MATCH:
                    self.username_entry.config(state=tk.DISABLED)
                    self.username_button.config(state=tk.DISABLED)
                    self.password_label.grid(row=1, column=0, pady=5, padx=2)
                    self.password_entry.grid(row=1, column=1, pady=5, padx=2)
                    self.password_button.grid(row=1, column=2, pady=5, padx=2)
                    self.window.update_idletasks()
                elif response.status == Status.NO_MATCH:
                    messagebox.showerror("Login Failed", "No such username exists! Please register for an account.")
                    self.window.destroy()
                    RegisterClient(server_socket)
                else:
                    messagebox.showerror("Error", "Unexpected server response.")
                    return

    def send_password(self):
        """Send password to server"""
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Input Error", "Password cannot be empty!")
            return
        username = self.username_entry.get()
        if not username:
            messagebox.showwarning("Input Error", "Username cannot be empty!")
            return
        
        request = DataObject(request=Request.CHECK_PASSWORD, datalen=2, data=[username, password])
        self.server_socket.sendall(request.serialize())
        data_buffer = b""
        received = False
        while not received:
            data = self.server_socket.recv(1024)
            if not data:
                messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
                self.close_connection()
                return
            data_buffer += data
            serial, data_buffer = DataObject.get_one(data_buffer)
            if serial != b"":
                received = True
                response = DataObject(method="serial", serial=serial)
                print(f"Received: {response.to_string()}")
                if response.status == Status.MATCH:
                    messagebox.showinfo("Success", "Login Successful!")
                    self.window.destroy()
                    UserClient(self.server_socket, username)
                elif response.status == Status.NO_MATCH:
                    messagebox.showerror("Login Failed", "Wrong password!")
                    return
                else:
                    messagebox.showerror("Error", "Unexpected server response.")
                    return

    def close_connection(self):
        self.server_socket.close()
        self.window.destroy()


class RegisterClient:
    def __init__(self, server_socket):
        self.window = tk.Tk()
        self.window.geometry("500x200")
        self.server_socket = server_socket
        self.window.title("Register")
        self.create_register_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.close_connection)
        self.window.mainloop()

    def create_register_ui(self):
        """Create the register UI"""
        self.username_label = tk.Label(self.window, text="Username:")
        self.username_label.grid(row=0, column=0, pady=5, padx=2)
        self.username_entry = tk.Entry(self.window)
        self.username_entry.grid(row=0, column=1, pady=5, padx=2)

        self.password_label = tk.Label(self.window, text="Password:")
        self.password_label.grid(row=1, column=0, pady=5, padx=2)
        self.password_entry = tk.Entry(self.window, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=2)

        self.confirm_password_label = tk.Label(self.window, text="Confirm Password:")
        self.confirm_password_label.grid(row=2, column=0, pady=5, padx=2)
        self.confirm_password_entry = tk.Entry(self.window, show="*")
        self.confirm_password_entry.grid(row=2, column=1, pady=5, padx=2)

        self.confirm_password_button = tk.Button(self.window, text="Register", command=self.send_new_user)
        self.confirm_password_button.grid(row=3, column=1, sticky="W", pady=10)

        self.window.update_idletasks()

    def send_new_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not username:
            messagebox.showwarning("Input Error", "Username cannot be empty!")
            return
        if " " in username:
            messagebox.showwarning("Input Error", "Username cannot contain spaces.")
            return
        if "%" in username:
            messagebox.showwarning("Input Error", "Username cannot contain '%'.")
            return
        if "_" in username:
            messagebox.showwarning("Input Error", "Username cannot contain '_'.")
            return
        if not password or not confirm_password:
            messagebox.showwarning("Input Error", "Password cannot be empty!")
            return
        if " " in password:
            messagebox.showwarning("Input Error", "Username cannot contain spaces.")
            return
        if password != confirm_password:
            messagebox.showwarning("Input Error", "Passwords must match!")
            return

        request = DataObject(request=Request.CREATE_USER, datalen=2, data=[username, password])
        self.server_socket.sendall(request.serialize())

        data_buffer = b""
        received = False
        while not received:
            data = self.server_socket.recv(1024)
            if not data:
                messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
                self.close_connection()
                return
            data_buffer += data
            serial, data_buffer = DataObject.get_one(data_buffer)
            if serial != b"":
                received = True
                response = DataObject(method="serial", serial=serial)
                print(f"Received: {response}")
                if response.status == Status.SUCCESS:
                    messagebox.showinfo("Success", "Registration Successful!")
                    self.window.destroy()
                    LoginClient(self.server_socket)
                elif response.status == Status.MATCH:
                    messagebox.showwarning("Error", "Username already exists.")
                    return
                else:
                    messagebox.showerror("Error", "Unexected server response.") 
                    return

    def close_connection(self):
        self.server_socket.close()
        self.window.destroy()


class UserClient:

    ACCOUNTS_LIST_LEN = 19

    def __init__(self, server_socket, username):
        self.pending_requests = {} # dictionary to track pending request confirmations: key = time (.1ms), value = request
        self.do_wait = False

        self.accounts = []
        self.accounts_offset = 0

        self.unread_count = 0
        self.message_count = 0

        self.username = username
        self.window = tk.Tk()
        self.window.geometry("1100x500")
        self.server_socket = server_socket
        self.window.title(f"{username}'s Chat")
        self.check_user_status()
        self.create_chat_ui()
        self.query_accounts()


        # Set up socket with event binding
        self.window.tk.createfilehandler(self.server_socket, tk.READABLE, self.handle_server_response)

        self.window.protocol("WM_DELETE_WINDOW", self.close_connection)
        self.window.mainloop()
    
    def create_chat_ui(self):        

        # Accounts column
        self.accounts_label = tk.Label(self.window, text="Accounts:")
        self.accounts_label.grid(row=0, column=0, sticky="W", padx=1, pady=5)

        self.accounts_searchbar = tk.Entry(self.window, width=20)
        self.accounts_searchbar.grid(row=0, column=1, padx=1, pady=5, sticky="W")

        self.accounts_search_button = tk.Button(self.window, text="Search", command=self.query_accounts)
        self.accounts_search_button.grid(row=0, column=2, padx=1, pady=5, sticky="W")

        self.accounts_list = tk.Text(self.window, wrap=tk.WORD, state=tk.DISABLED, height=20, width=50)
        self.accounts_list.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="W")

        self.accounts_back_button = tk.Button(self.window, text="<", command=self.prev_account)
        self.accounts_back_button.grid(row=2, column=0, pady=1, sticky="W")
        self.accounts_next_button = tk.Button(self.window, text=">", command=self.next_account)
        self.accounts_next_button.grid(row=2, column=2, pady=1, sticky="E")

        # Messages column
        self.unread_count_label = tk.Label(self.window, text=f"You have {self.unread_count} unread messages. How many would you like to read?")
        self.unread_count_label.grid(row=0, column=3, padx=10, pady=5, sticky="E")

        self.unread_count_entry = tk.Entry(self.window, width=5)
        self.unread_count_entry.grid(row=0, column=4, padx=2, pady=5, sticky="W")

        self.read_button = tk.Button(self.window, text="Read Messages")
        self.read_button.grid(row=0, column=5, padx=5, pady=5, sticky="W")

        self.chat_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state=tk.DISABLED, height=20, width=90)
        self.chat_area.grid(row=1, column=3, columnspan=3, padx=10, pady=5, sticky="W")

        self.window.update_idletasks()

    def check_user_status(self):
        data_buffer = b""
        received = False
        while not received:
            data = self.server_socket.recv(1024) # num unread message, num total messages
            if not data:
                messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
                self.close_connection()
                return 
            data_buffer += data
            serial, data_buffer = DataObject.get_one(data_buffer)
            if serial != b"":
                received = True
                response = DataObject(method="serial", serial=serial)
                print(f"Response: {response.to_string()}")
                if response.request != Request.CONFIRM_LOGIN:
                    messagebox.showerror("Server Error", "Login Failed. An unexpected communication has occurred.")
                    self.window.destroy()
                    LoginClient(self.server_socket)
                    return
                if response.status == Status.SUCCESS:
                    messagebox.showinfo("Sucess", "Logged In")
                    self.unread_count, self.message_count = int(response.data[0]), int(response.data[1])
                elif response.status == Status.MATCH:
                    messagebox.showerror("Error", "Already Logged In Elsewhere")
                    self.window.destroy()
                    LoginClient(self.server_socket)
                    return

    def query_accounts(self):
        pattern = self.accounts_searchbar.get().strip()
        data = ["All"] if not pattern else ["Like"] + [pattern]

        request_id = round(time.time() * 10000)  # Unique request ID
        request = DataObject(user=self.username, request=Request.GET_USERS, datalen=len(data), data=data, sequence=request_id)
        print(f"Sending: {request.to_string()}")
        self.server_socket.sendall(request.serialize())

        # Store pending confirmation event
        self.pending_requests[request_id] = request.request
        self.do_wait = True

        self.window.after(100, self.wait_for_confirmation, request_id)
    
    def display_accounts(self):
        self.accounts_list.config(state=tk.NORMAL)
        self.accounts_list.delete(1.0, tk.END)
        self.accounts_list.config(state=tk.DISABLED)
        
        if self.ACCOUNTS_LIST_LEN + self.accounts_offset >= len(self.accounts):
            self.accounts_next_button.config(state=tk.DISABLED)
        else:
            self.accounts_next_button.config(state=tk.NORMAL)
        if self.accounts_offset == 0:
            self.accounts_back_button.config(state=tk.DISABLED)
        else:
            self.accounts_back_button.config(state=tk.NORMAL)

        for i in range(self.accounts_offset, min(self.ACCOUNTS_LIST_LEN + self.accounts_offset, len(self.accounts))):
            self.accounts_list.config(state=tk.NORMAL)
            self.accounts_list.insert(tk.END, self.accounts[i] + "\n")
            self.accounts_list.config(state=tk.DISABLED)
    
    def next_account(self):
        self.accounts_offset += self.ACCOUNTS_LIST_LEN
        if self.ACCOUNTS_LIST_LEN + self.accounts_offset >= len(self.accounts):
            self.accounts_next_button.config(state=tk.DISABLED)
        else:
            self.accounts_next_button.config(state=tk.NORMAL)
        if self.accounts_offset == 0:
            self.accounts_back_button.config(state=tk.DISABLED)
        else:
            self.accounts_back_button.config(state=tk.NORMAL)
        self.display_accounts()
    
    def prev_account(self):
        self.accounts_offset -= self.ACCOUNTS_LIST_LEN
        if self.ACCOUNTS_LIST_LEN + self.accounts_offset >= len(self.accounts):
            self.accounts_next_button.config(state=tk.DISABLED)
        else:
            self.accounts_next_button.config(state=tk.NORMAL)
        if self.accounts_offset == 0:
            self.accounts_back_button.config(state=tk.DISABLED)
        else:
            self.accounts_back_button.config(state=tk.NORMAL)
        self.display_accounts()
            
    def display_message(self, response):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, response + "\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def read_messages(self):
        num_to_read = self.unread_count_entry.get().strip()

        if not num_to_read or not num_to_read.isdigit() or int(num_to_read) < 1 or int(num_to_read) > self.unread_count:
            messagebox.showwarning("Input Error", f"Must be a number from 1 to {self.unread_count}")
            return

    # def send_message(self):
    #     message = self.message_entry.get().strip()

    #     if not message:
    #         messagebox.showwarning("Input Error", "Message cannot be empty!")
    #         return

    #     request_id = round(time.time() * 10000)  # Unique request ID
    #     request = DataObject(user=self.username, sequence=request_id)

    #     if message == "get":
    #         request.update(request=Request.GET_USERS)
    #     elif message == "getonline":
    #         request.update(request=Request.GET_ONLINE_USERS)
    #     # elif message[:7] == "message":
    #     #     request.update(request=Request.SEND_MESSAGE)
    #     else:
    #         request.update(request=Request.ALERT_MESSAGE, datalen=1, data=[message])
        
    #     print(f"Sending {request.to_string()}")
    #     self.server_socket.sendall(request.serialize())

    #     # Store pending confirmation event
    #     self.pending_requests[request_id] = request.request
    #     self.do_wait = True

    #     # Check for confirmation every 100ms without freezing the UI
    #     self.window.after(100, self.wait_for_confirmation, request_id)

    def wait_for_confirmation(self, request_id):
        if self.do_wait:
            if request_id in self.pending_requests:
                self.window.after(100, self.wait_for_confirmation, request_id)
            else:
                self.do_wait = False
    
    def handle_server_response(self, file, event):
        try:
            data_buffer = b""
            data = self.server_socket.recv(1024)
            if not data:
                messagebox.showerror("Server Error", "Connection closed by server.")
                self.close_connection()
                return

            data_buffer += data
            serial, data_buffer = DataObject.get_one(data_buffer)
            while serial != b"":
                response = DataObject(method="serial", serial=serial)
                print(f"Response:{response.to_string()}")

                if response.sequence in self.pending_requests:
                    if response.request == self.pending_requests[response.sequence]:
                        if response.request == Request.GET_USERS:
                            if response.status == Status.SUCCESS:
                                self.accounts = response.data
                                self.display_accounts()
                            else:
                                messagebox.showerror("Error", "An error has occurred.")
                        del self.pending_requests[response.sequence]
                else:
                    # handle new incoming messages
                    pass

                serial, data_buffer = DataObject.get_one(data_buffer)

        except BlockingIOError:
            pass

    def close_connection(self):
        self.server_socket.close()
        self.window.destroy()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py HOSTNAME PORTNAME")
        exit(1)
    host, port = sys.argv[1], int(sys.argv[2])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, int(port)))

    LoginClient(server_socket)
