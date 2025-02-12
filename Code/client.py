import socket
import sys
import selectors
import time
from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk
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
        self.request_counter = 0
        self.data_buffer = b""
        self.pending_requests = {} # dictionary to track pending request confirmations: key = time (.1ms), value = request
        self.do_wait = False

        self.accounts = []
        self.accounts_offset = 0

        self.unread_count = 0
        self.message_count = 0

        self.username = username
        self.window = tk.Tk()
        self.window.geometry("1500x500")
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
        self.message_count_label = tk.Label(self.window, text=f"You have {self.message_count} messages ({self.unread_count} unread). How many messages would you like to see?")
        self.message_count_label.grid(row=0, column=3, padx=2, pady=5, sticky="E")

        self.message_count_entry = tk.Entry(self.window, width=5)
        self.message_count_entry.grid(row=0, column=4, padx=2, pady=5, sticky="W")

        self.read_button = tk.Button(self.window, text="Show Messages", command=self.query_messages)
        self.read_button.grid(row=0, column=5, padx=2, pady=5, sticky="W")

        # Display messages
        self.chat_area = ttk.Treeview(self.window, columns=("ID", "Time", "Sender", "Subject", "Body"), show="headings", height=15)
        self.chat_area.heading("Time", text="Time", anchor="w")
        self.chat_area.heading("Sender", text="Sender", anchor="w")
        self.chat_area.heading("Subject", text="Subject", anchor="w")
        self.chat_area.column("ID", width=0, stretch=False)
        self.chat_area.column("Time", width=125, stretch=False)
        self.chat_area.column("Sender", width=175, anchor="w", stretch=False)
        self.chat_area.column("Subject", width=350, anchor="w", stretch=False)
        self.chat_area.column("Body", width=0, stretch=False)

        # Scrollbar for Chat Treeview
        self.chat_scroll = ttk.Scrollbar(self.window, orient="vertical", command=self.chat_area.yview)
        self.chat_area.configure(yscroll=self.chat_scroll.set)

        self.chat_area.grid(row=1, column=3, columnspan=3, padx=10, pady=5, sticky="W")
        self.chat_scroll.grid(row=1, column=6, sticky="NS")

        # Bind click event
        self.chat_area.bind("<Double-1>", self.open_message)

        # Send Message UI
        send_frame = tk.Frame(self.window)
        send_frame.grid(row=0, column=7, rowspan=3, padx=20, pady=10, sticky="N")

        tk.Label(send_frame, text="Send a Message").grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(send_frame, text="To:").grid(row=1, column=0, sticky="E", padx=5)
        self.recipient_entry = tk.Entry(send_frame, width=30)
        self.recipient_entry.grid(row=1, column=1, pady=2, sticky="W")

        tk.Label(send_frame, text="Subject:").grid(row=2, column=0, sticky="E", padx=5)
        self.subject_entry = tk.Entry(send_frame, width=30)
        self.subject_entry.grid(row=2, column=1, pady=2, sticky="W")

        tk.Label(send_frame, text="Body:").grid(row=3, column=0, sticky="NE", padx=5)
        self.body_text = tk.Text(send_frame, wrap=tk.WORD, height=15, width=39)
        self.body_text.grid(row=3, column=1, pady=2, sticky="W")

        self.send_button = tk.Button(send_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=4, column=1, pady=5, sticky="W")
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

        self.request_counter += 1
        request_id = self.request_counter
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

    def query_messages(self):
        for item in self.chat_area.get_children():
            self.chat_area.delete(item)

        num_to_read = self.message_count_entry.get().strip()
        if not num_to_read or not num_to_read.isdigit() or int(num_to_read) < 1 or int(num_to_read) > self.message_count:
            messagebox.showwarning("Input Error", f"Must be a number from 1 to {self.message_count}")
            return
        
        self.request_counter += 1
        request_id = self.request_counter
        request = DataObject(user=self.username, request=Request.GET_MESSAGE, datalen=2, data=["0", num_to_read], sequence=request_id)
        print(f"Sending: {request.to_string()}")
        self.server_socket.sendall(request.serialize())

        # Store pending confirmation event
        self.pending_requests[request_id] = request.request
        self.do_wait = True

        self.window.after(100, self.wait_for_confirmation, request_id)
            
    def display_messages(self, messages):
        for serial in messages:
            serial = serial.encode("utf-8")
            message = MessageObject(method="serial", serial=serial)
            formatted_datetime = datetime.fromisoformat(message.time_sent).strftime("%-m/%-d/%y %-H:%M")
            formatted_datetime = f"{formatted_datetime:>15}"  
            formatted_datetime += " (*)" if not message.read else "    "  # 4 spaces to match (*)

            self.chat_area.insert("", "end", values=(message.id, formatted_datetime, message.sender, message.subject, message.body))

    def open_message(self, event):
        item = self.chat_area.identify_row(event.y)
        if item:
            message_id, time_sent, sender, subject, body = self.chat_area.item(item, "values") 

            self.window.update_idletasks()
            
            message_window = tk.Toplevel(self.window)
            message_window.title(f"Message from {sender}: {subject}")
            message_window.geometry("600x400")

            message_textbox = tk.Text(message_window, wrap=tk.WORD, height=20, width=70)
            message_textbox.pack(expand=True, fill="both", padx=10, pady=10)

            message_textbox.config(state=tk.NORMAL)
            message_textbox.insert(
                tk.END,
                f"{'Time:':<8} {time_sent.strip().replace('(*)', '')}\n"
                f"{'From:':<8} {sender}\n"
                f"{'To:':<8} {self.username}\n\n"
                f"Subject: {subject}\n\n"
                f"Body:\n\n{body}"
            )
            message_textbox.config(state=tk.DISABLED)

            message_window.transient(self.window)
            message_window.grab_set()

            self.request_counter += 1
            request_id = self.request_counter
            request = DataObject(user=self.username, request=Request.CONFIRM_READ, datalen=1, data=[message_id], sequence=request_id)
            print(f"Sending: {request.to_string()}")
            self.server_socket.sendall(request.serialize())

            # Store pending confirmation event
            self.pending_requests[request_id] = request.request
            self.do_wait = True

            self.window.after(100, self.wait_for_confirmation, request_id)
    
    def send_message(self):
        recipient = self.recipient_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", tk.END).strip()  # Get text from Text widget
        if not recipient or not subject or not body:
            messagebox.showwarning("Warning", "All fields are required!")
            return
        
        current_time = datetime.now(timezone.utc)
        iso_time = current_time.isoformat(timespec='seconds')
        
        message = MessageObject(sender=self.username, recipient=recipient, time=iso_time, subject=subject, body=body)
        message_string = message.serialize().decode("utf-8")
        print(f"Message:{message.to_string()}")

        self.request_counter += 1
        request_id = self.request_counter
        request = DataObject(user=self.username, request=Request.SEND_MESSAGE, datalen=1, data=[message_string], sequence=request_id)

        print(f"Sending: {request.to_string()}")
        self.server_socket.sendall(request.serialize())

        # Store pending confirmation event
        self.pending_requests[request_id] = request.request
        self.do_wait = True

        # Clear fields after sending
        self.recipient_entry.delete(0, tk.END)
        self.subject_entry.delete(0, tk.END)
        self.body_text.delete("1.0", tk.END)

        self.window.after(100, self.wait_for_confirmation, request_id)

    def wait_for_confirmation(self, request_id):
        if self.do_wait:
            if request_id in self.pending_requests:
                self.window.after(100, self.wait_for_confirmation, request_id)
            else:
                self.do_wait = False
    
    def handle_server_response(self, file, event):
        try:
            data = self.server_socket.recv(1024)
            if not data:
                messagebox.showerror("Server Error", "Connection closed by server.")
                self.close_connection()
                return

            self.data_buffer += data
            serial, self.data_buffer = DataObject.get_one(self.data_buffer)
            while serial != b"":
                response = DataObject(method="serial", serial=serial)
                print(f"Response:{response.to_string()}")

                if response.sequence in self.pending_requests:
                    if response.request == self.pending_requests[response.sequence]:
                        if response.request == Request.GET_USERS:
                            if response.status == Status.SUCCESS:
                                self.accounts = [account for account in response.data if account != self.username]
                                self.display_accounts()
                            else:
                                messagebox.showerror("Error", "An error has occurred while finding other users.")
                        elif response.request == Request.GET_MESSAGE:
                            if response.status == Status.SUCCESS:
                                self.display_messages(response.data)
                            else:
                                messagebox.showerror("Error", "An error has occurred while getting your messages.")
                        elif response.request == Request.CONFIRM_READ:
                            if response.status == Status.SUCCESS:
                                self.query_messages()
                        elif response.request == Request.SEND_MESSAGE:
                            if response.status == Status.SUCCESS:
                                messagebox.showinfo("Sent", "Your message has been sent")
                            else:
                                messagebox.showerror("Error", "An error has occurred while sending your message.")
                        del self.pending_requests[response.sequence]
                else:
                    # handle new incoming messages
                    if response.request == Request.ALERT_MESSAGE:
                        if response.status == Status.SUCCESS:
                            pass

                serial, self.data_buffer = DataObject.get_one(self.data_buffer)

        except BlockingIOError:
            pass

    def close_connection(self):
        self.server_socket.close()
        self.window.destroy()

#^ DELETE MESSAGE: takes in one message id, returns status success


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py HOSTNAME PORTNAME")
        exit(1)
    host, port = sys.argv[1], int(sys.argv[2])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, int(port)))

    LoginClient(server_socket)
