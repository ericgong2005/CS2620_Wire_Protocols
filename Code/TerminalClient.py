import socket
import sys
import selectors
from datetime import datetime, timezone

from Modules.Flags import Request, Status
from Modules.DataObjects import DataObject, MessageObject
from Modules.SelectorData import SelectorData

# run python client.py HOSTNAME PORTNAME

def client_user(server_socket, username):
    data_buffer = b""
    logged_in = False
    while not logged_in:
        data = server_socket.recv(1024)
        if not data:
            print("Connection closed by the server.")
            return
        data_buffer += data
        serial, data_buffer = DataObject.get_one(data_buffer)
        if serial != b"":
            logged_in = True
            response = DataObject(method="serial", serial=serial)
            print(f"{response.to_string()}")
            if response.request != Request.CONFIRM_LOGIN:
                print("Unexpected Communication, Login Failed")
                return
            if response.status == Status.SUCCESS:
                print("Logged In")
            elif response.status == Status.MATCH:
                print("Already Logged In Elsewhere")
                return
            else:
                print("Login Failed")
                return
    
    # Use selectors to allow for polling instead of blocking
    client_selector = selectors.DefaultSelector()
    client_selector.register(server_socket, selectors.EVENT_READ, data=SelectorData("User"))
    server_socket.setblocking(False)

    while logged_in:
        # Send user input to database
        command = input(f"Enter a message as User {username}: ")
        if command == "exit":
            break
        lines = command.split()
        request = DataObject(user=username)
        if lines[0] == "get":
            request.update(request=Request.GET_ONLINE_USERS)
        if lines[0] == "msg":
            request.update(request=Request.GET_MESSAGE, datalen=3, data=[lines[1], lines[2], lines[3]])
            # start index, # messages, read/unread
        elif lines[0] == "users":
            request.update(request=Request.GET_USERS, datalen=1, data = ["All"])
        elif lines[0] == "like":
            request.update(request=Request.GET_USERS, datalen=2, data = ["Like", lines[1]])
        elif lines[0] == "delete":
            request.update(request=Request.DELETE_USER)
        elif lines[0] == "logout":
            request.update(request=Request.CONFIRM_LOGOUT)
            logged_in = False
        elif lines[0] == "read":
            request.update(request=Request.CONFIRM_READ, datalen=len(lines[1:]), data=lines[1:])
        elif lines[0] == "message":
            recipient = input("Send Message To: ")
            subject = input("Enter Message Subject: ")
            body = input("Enter Message Body: ")
            current_time = datetime.now(timezone.utc)
            iso_time = current_time.isoformat(timespec='seconds')
            message = MessageObject(sender=username, recipient=recipient, time=iso_time, subject=subject, body=body)
            message_string = message.serialize().decode("utf-8")
            print(message.to_string())
            request.update(request=Request.SEND_MESSAGE, datalen=1, data=[message_string])
        else:
            request.update(request=Request.ALERT_MESSAGE, datalen=1, data=[command])
        
        print(f"Sending {request.to_string()}")

        server_socket.sendall(request.serialize())

        # Get response(s)
        events = client_selector.select(timeout=None)
        for key, mask in events:
            if mask & selectors.EVENT_READ:
                data = key.fileobj.recv(1024)
                if not data:
                    print("Connection closed by the server.")
                    return
                key.data.inbound += data
                serial, key.data.inbound = DataObject.get_one(key.data.inbound)
                while serial != b"":
                    response = DataObject(method="serial", serial=serial)
                    if response.request in [Request.DELETE_USER, Request.CONFIRM_LOGOUT] :
                        return
                    print(response.to_string()) 
                    serial, key.data.inbound = DataObject.get_one(key.data.inbound)
                    

def client_create_user(server_socket):
    username = ""
    while True:
        print("Create New User:")
        username = input("Enter Username: ")
        password = input("Enter Password: ")
        confirm_password = input("Confirm Password: ")
        if password == confirm_password:
            request = DataObject(request=Request.CREATE_USER, datalen=2, data=[username, password])
            server_socket.sendall(request.serialize())
        else:
           messagebox.showerror("Error", "Unexpected server response.") 

    def close_connection(self):
        self.server_socket.close()
        self.window.destroy()


class ChatClient:
    def __init__(self, server_socket):
        self.window = tk.Tk()
        self.server_socket = server_socket
        self.window.title("Chat")
        self.create_chat_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.close_connection)
        self.window.mainloop()
    
    def create_chat_ui(self):
        self.chat_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state=tk.DISABLED, height=15, width=50)
        self.chat_area.pack(pady=10)

        self.message_entry = tk.Entry(self.window, width=40)
        self.message_entry.pack(pady=5, side=tk.LEFT)
        self.send_button = tk.Button(self.window, text="Send", command=self.send_message)
        self.send_button.pack(pady=5, side=tk.RIGHT)
        self.check_user_status()

    def check_user_status(self):
        response = server_socket.recv(1024).decode("utf-8")
        self.display_message(response)
        if response == "Logged In":
            messagebox.showinfo("Success", "Logged In")
        elif response == "Duplicate":
            messagebox.showerror("Error", "Already Logged In Elsewhere")
            self.window.destroy()
            LoginClient(self.server_socket)
            return
        else:
            messagebox.showerror("Error", "Login Failed")
            self.window.destroy()
            LoginClient(self.server_socket)
            return
    
    def send_message(self):
        message = self.message_entry.get()

        if not message:
            messagebox.showwarning("Input Error", "Message cannot be empty!")
            return
        
        self.server_socket.sendall(message.encode("utf-8"))
        self.display_message(f"You: {message}")
        self.message_entry.delete(0, tk.END)

        response = self.server_socket.recv(1024)
        if not response:
            messagebox.showerror("Server Error", "Connection closed by server. Please restart the app.")
            self.window.destroy()
            return
        response = response.decode("utf-8")
        print(f"Received {response}")
        self.display_message(f"Server: {response}")
    
    def display_message(self, response):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, response + "\n")
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
    server_socket.connect((host, int(port)))

    LoginClient(server_socket)
