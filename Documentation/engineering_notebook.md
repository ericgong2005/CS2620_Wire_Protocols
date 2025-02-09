# Engineering Notebook

## Contents
- Quick notes
- Planning
- Changes
- Code Version logs
- Planning Version 1
- Planning Version 2
- Planning Verison 3

## Quick Notes
- Remember to hash the password
- Remember to implement an event waiting on the database process startup

## Planning
We split the plan down into a couple modularized and separate implementations. This will ensure that each portion can be changed with minimal impact on other components, as well increase our ability to remain organized.

### Key Components:
- Organization
- Database
- Client-Server communication setup
- Logins
- Standardized object for information transfer
- Handling and displaying messages
- Account Deletion

### Organization
- Put helper functions and constants and class definitions into the Modules folder, which interpreted as a package
- Put tests into Tests folder, also a package
- tests.py to run tests in the Test folder
- server_daemon.py and client.py in the Code folder where Tests and Modules are located

### Database:
- access everything using SQLite on .db files
- one passwords.db file with username-password pairs (not plaintext passwords, of course)
    - have entries for Username and hashed_password
- one messages.db file with messages
    - have sender, reciever, time sent, delivered, subject, message
- one users.db with usernames and maybe things like # of undelivered messages
- have one process to query the database to prevent issues on concurrency
- have a database class with the necessary functions
- make sure that the database class contains \_\_exit\_\_ definitions so the .db doesn't get corrupted
- For processes to communicate with the databse process, create a new pipe for each communication and close it immediately when done to avoid dealing with the semantics of leaving a pipe open and getting inturrupted
    - However, should figure out how to keep the pipe open and figure out the correct error catching, both for efficiency, and also due to the fact that the program would break if an interrupt came in at the moment before the pipe is closed in the current implementation.


### Client-Server communication setup:
Client specifications:
- The client, upon launch, should attempt to connect to the server
- If successful, the client can switch to the "handling and displaying messages" component

Server specifications:
- The server should run a Daemon process to handle incoming connections
- Upon connection, the server should fork a child to handle logins
- The login child, upon sucess can switch to a user child that will handle client requests on the server, etc.
- The process of having children will ensure the server can handle multiple clients

Bonus features:
- The layers of children will allow for chrooting to restrict access to sensitive files

### Logins:
Specifications:
- The login should be handled on the server end by a special login process that will send a message asking for the user's login info
- The usernames should be stored in plaintext, and the passwords a hashed version of the user's password
- The passwords file should be a .db with username, hashed_password

Login steps:
- The client will start the connection, but the login process will initiate communication, asking for a username
- The client prompts the user for a username
- The login process recieves the username and checks for the username
- If the username exists:
    - The login process asks the database process to check the username-hashedpassword pair
    - The password is sent, encrypted with a constant string or with the user's username as the symmetric key
    - The login process confirms the password by hashing it and comparing against the variable
    - If fails, then tell the client, otherwise, inform the client of success and fork a user child
- If the username does not exist:
    - The login process asks the user to create a password
    - The password is sent, encrypted with a constant string or with the user's username as the symmetric key
    - The database process writes the username-hashed-password pair to the file
    - Then allow for login again

Bonus features:
- Timeout's can be implemented on both ends: the client closes connection if it does not hear the login process send a message, and the login process kills itself if no login attempt occurs within 60 seconds
- Encrypt the entire passwords file
- Negotiate (via Diffie-hellman) a symetric key for encrypting messages, passing the negotiated key to the serialize method.

### Standardized Objects for information transfer
Specification:
- Type field, with possible values "System", "Login", "Message"
- Data field:
    - System
        - Used to confirm switch to login or child process, have a keyword string to confirm, or the word failed
        - Used to tell the client whether to get the password or ask for a new password (depending on whether the user is logging in or creating an account)
    
    - Login
        - used to send the username or password to the login process
        - contains a type (username/password) and the value
    
    - Message
        - used to send a message
        - Contains sender, recipient, time sent, subject, and message
- Implement a custom and a json serializer/deserializer as a stand-alone function
    - could contain a flag on type (ie json or custom) so the serializer/deserializer can handle either

### Handling and displaying messages
Sending:
- The client populates the message object, serializes it and sends it to the user process on the server
- The user process deserializes the message and submits it to the database process for insertion
- The database process confirms the recipient exists, if not, then it changes the recipient to the sender, adding a note on how the send failed
- The data process confirms the sender exists. If not, then something has really gone wrong, and the user process should send a fatal error message to the client, and kill itself
- The user process sends a confirmation to the client

Receiving:
- The user process, upon logging in, requests the database process for undelivered messages
- Need some sort of new-message indicator for the user process, managed by the database process

Deleting messages:
- The user process makes the database process delete the messages

Deleting accounts:
- The client process freezes when the deletion begins
- The database process goes through all undelivered, recieved messages, changing the recipent to the sender, adding a note that the account was deleted before the message could be delivered, and follow the sending process
- The user process sends a confirmation to the client, which switches to the login page
- The user process kills itself

## Changes
A log of changes, ideas and observations to the plan

- Decided to use multithreading to modularize the code and have each user be a separate process
- Use the multiprocessing python library over os.form to ensure support outside of UNIX
    - Want to use forkserve, but may not be supported on windows, so spawn is used (fork may causes crashes, according to the [documentation](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing))
- Migrate to using .db files for chat message storage, instead of serialized files:
    - Having a single process for accessing the .db files will prevent issues on concurrency
    - Copy of old ideas in Version 1
- Best practice to ensure the passwordhash is as hidden as possible. Move the checking of the password to the database class in the database process, not letting the login process see the passwordhash at all
- Change the use of pipes to sockets for support on windows


## Code Version Logs
- Version1:
    - Version1 client and server_daemon contain a base framework for logging in
    - Daemon unaffected by login_process and user_process errors
    - Multiple users can connect at once
    - No rigorous testing yet, only tried via terminal
    - Does not support the creation of new users
    - stores passwords in a .csv file
    - passwords currently plaintext
- Version2:
    - Daemon unaffected by login_process and user_process errors
    - Multiple users can connect at once
    - Some rigorous testing
    - Support the creation of new users
    - stores passwords in a .db file
    - passwords currently plaintext

## Planning Version 1
We split the plan down into a couple modularized and separate implementations. This will ensure that each portion can be changed with minimal impact on other components, as well increase our ability to remain organized.

### Key Components:
- File organization
- Client-Server communication setup
- Logins
- Standardized object for information transfer
- Handling and displaying messages
- Account Deletion

### File Organization:
- one folder containing a file with username-password pairs (not plaintext passwords, of course)
- one folder with sub-folders for each user
    - each user's folder should contain:
        - a folder with serialized message objects for messages sent to them, one object per file
        - a file containing a list of message paths for messages that have been sent by the user
        - a file containing a list of the messages sent to the user, alongside status (delivered or not)

### Client-Server communication setup:
Client specifications:
- The client, upon launch, should attempt to connect to the server
- If successful, the client can switch to the "handling and displaying messages" component

Server specifications:
- The server should run a Daemon process to handle incoming connections
- Upon connection, the server should fork a child to handle logins
- The login child, upon sucess can switch to a user child that will handle client requests on the server, etc.
- It will be important to ensure proper locking of files (perhaps file-level granularity) to prevent race conditions
    - Will need some sort of global variable/object for locking files for writes, and a separate global variable for locking the gobal variable/object
    - Could do user-folder-level granularity for simplicity
    - The global object can also contain a new-messages counter to indicate it has been written to
- The process of having children will ensure the server can handle multiple clients

Bonus features:
- The layers of children will allow for chrooting to restrict access to sensitive files

### Logins:
Specifications:
- The login should be handled on the server end by a special login process that will send a message asking for the user's login info
- The usernames should be stored in plaintext, and the passwords a hashed version of the user's password
- The passwords file should be a csv with username, hashed_password on each line

Login steps:
- The client will start the connection, but the login process will initiate communication, asking for a username
- The client prompts the user for a username
- The login process recieves the username and checks for the username
- If the username exists:
    - The login process saves the hashed password to a variable
    - The login process prompts the client to fetch the password
    - The password is sent, encrypted with a constant string or with the user's username as the symmetric key
    - The login process confirms the password by hashing it and comparing against the variable
    - If fails, then tell the client, otherwise, inform the client of success and fork a user child
- If the username does not exist:
    - The login process asks the user to create a password
    - The password is sent, encrypted with a constant string or with the user's username as the symmetric key
    - The login process locks the password file and writes the username-hashed-password pair to the file
    - The login process adds the user's folder, and adds it to the global object for locking files
    - Then for a user child like normal

Bonus features:
- Timeout's can be implemented on both ends: the client closes connection if it does not hear the login process send a message, and the login process kills itself if no login attempt occurs within 60 seconds
- Encrypt the entire passwords file
- Negotiate (via Diffie-hellman) a symetric key for encrypting messages, passing the negotiated key to the serialize method.

### Standardized Objects for information transfer
Specification:
- Operation field, with possible values "Version", "System", "Login", "Message"
- Data field:
    - System
        - Used to confirm switch to login or child process, have a keyword string to confirm, or the word failed
        - Used to tell the client whether to get the password or ask for a new password (depending on whether the user is logging in or creating an account)
    
    - Login
        - used to send the username or password to the login process
        - contains a type (username/password) and the value
    
    - Message
        - used to send a message
        - Contains sender, recipient, time sent, subject, and message
- Implement a custom and a json serializer/deserializer as a stand-alone function
    - could contain a flag on type (ie json or custom) so the serializer/deserializer can handle either

### Handling and displaying messages
Sending:
- The client populates the message object, serializes it and sends it to the user process on the server
- The user process deserializes the message and extracts sender, reciever and send time
- The user process recieves the serialized object, and turns it into a file
    - The file should have a name consisting of the sender, recipient and send time to be uniquely named
- The user process confirms the recipient exists, if not, then it changes the recipient to the sender, adding a note on how the send failed
- The user process confirms the sender exists. If not, then something has really gone wrong, and the user process shoudl send a fatal error message to the client, and kill itself
- The user process locks the recipient folder, and adds the message in, then adds the message as an undelivered message to list of messages file, incrementing the new_message counter
- The user process locks the sender folder and adds the sent message path to the list of sent messages
- The user process sends a confirmation to the client

Receiving:
- The user process, upon logging in, serializes all the appropriate messages and sends it to the client by refering to the list of recieved messages
- The user process periodically checks the new_message counter. If it is non-zero, the process locks the folder and sends the new messages to the client, decrementing the new_message counter

Deleting messages:
- The user process locks the user's folder, deleting the message files, and removing their entries from the list of recieved messages
- The user process goes through all the sender's folders, locking them, and deleting the message from the list of sent messages

Deleting accounts:
- The client process freezes when the deletion begins
- The user process goes through all undelivered, recieved messages, changing the recipent to the sender, adding a note that the account was deleted before the message could be delivered, and follow the sending process
- The user process looks at the list of sent messages, and goes through all the recipient folders, locking them, and deleting the messages, as well as updating the entries to the recieved messages list
- The user process locks and deletes the user's folder
- The user process sends a confirmation to the client, which switches to the login page
- The user process kills itself

Notes:
- There may be some race conditions with deleting files and folders, if another client is attempting to read from them, or access the files. Thus we will need to think about whether or not we want to lock reading as well for deletion, in which case we will want to implement a reader-count (itself needing a lock), and a read lock (that would need to wait until reader-count = 0, and new processes cannot read when read lock is locked)

## Planning Version 2
We split the plan down into a couple modularized and separate implementations. This will ensure that each portion can be changed with minimal impact on other components, as well increase our ability to remain organized.

### Key Components:
- Organization
- Database
- Client-Server communication setup
- Logins
- Standardized object for information transfer
- Handling and displaying messages
- Account Deletion

### Organization
- Put helper functions and constants and class definitions into the Modules folder, which interpreted as a package
- Put tests into Tests folder, also a package
- tests.py to run tests in the Test folder
- server_daemon.py and client.py in the Code folder where Tests and Modules are located

### Database:
- access everything using SQLite on .db files
- one passwords.db file with username-password pairs (not plaintext passwords, of course)
    - have entries for Username and hashed_password
- one messages.db file with messages
    - have sender, reciever, time sent, delivered, subject, message
- one users.db with usernames and maybe things like # of undelivered messages
- have one process to query the database to prevent issues on concurrency
- have a database class with the necessary functions
- make sure that the database class contains \_\_exit\_\_ definitions so the .db doesn't get corrupted
- For processes to communicate with the databse process, create a new pipe for each communication and close it immediately when done to avoid dealing with the semantics of leaving a pipe open and getting inturrupted
    - However, should figure out how to keep the pipe open and figure out the correct error catching, both for efficiency, and also due to the fact that the program would break if an interrupt came in at the moment before the pipe is closed in the current implementation.

### Client-Server communication setup:
Client specifications:
- The client, upon launch, should attempt to connect to the server
- If successful, the client can switch to the "handling and displaying messages" component

Server specifications:
- The server should run a Daemon process to handle incoming connections
- Upon connection, the server should fork a child to handle logins
- The login child, upon sucess can switch to a user child that will handle client requests on the server, etc.
- The process of having children will ensure the server can handle multiple clients

Bonus features:
- The layers of children will allow for chrooting to restrict access to sensitive files

### Logins:
Specifications:
- The login should be handled on the server end by a special login process that will send a message asking for the user's login info
- The usernames should be stored in plaintext, and the passwords a hashed version of the user's password
- The passwords file should be a .db with username, hashed_password

Login steps:
- The client will start the connection, but the login process will initiate communication, asking for a username
- The client prompts the user for a username
- The login process recieves the username and checks for the username
- If the username exists:
    - The login process saves the hashed password to a variable
    - The login process prompts the client to fetch the password
    - The password is sent, encrypted with a constant string or with the user's username as the symmetric key
    - The login process confirms the password by hashing it and comparing against the variable
    - If fails, then tell the client, otherwise, inform the client of success and fork a user child
- If the username does not exist:
    - The login process asks the user to create a password
    - The password is sent, encrypted with a constant string or with the user's username as the symmetric key
    - The database process writes the username-hashed-password pair to the file
    - Then allow for login again

Bonus features:
- Timeout's can be implemented on both ends: the client closes connection if it does not hear the login process send a message, and the login process kills itself if no login attempt occurs within 60 seconds
- Encrypt the entire passwords file
- Negotiate (via Diffie-hellman) a symetric key for encrypting messages, passing the negotiated key to the serialize method.

### Standardized Objects for information transfer
Specification:
- Type field, with possible values "System", "Login", "Message"
- Data field:
    - System
        - Used to confirm switch to login or child process, have a keyword string to confirm, or the word failed
        - Used to tell the client whether to get the password or ask for a new password (depending on whether the user is logging in or creating an account)
    
    - Login
        - used to send the username or password to the login process
        - contains a type (username/password) and the value
    
    - Message
        - used to send a message
        - Contains sender, recipient, time sent, subject, and message
- Implement a custom and a json serializer/deserializer as a stand-alone function
    - could contain a flag on type (ie json or custom) so the serializer/deserializer can handle either

### Handling and displaying messages
Sending:
- The client populates the message object, serializes it and sends it to the user process on the server
- The user process deserializes the message and submits it to the database process for insertion
- The database process confirms the recipient exists, if not, then it changes the recipient to the sender, adding a note on how the send failed
- The data process confirms the sender exists. If not, then something has really gone wrong, and the user process should send a fatal error message to the client, and kill itself
- The user process sends a confirmation to the client

Receiving:
- The user process, upon logging in, requests the database process for undelivered messages
- Need some sort of new-message indicator for the user process, managed by the database process

Deleting messages:
- The user process makes the database process delete the messages

Deleting accounts:
- The client process freezes when the deletion begins
- The database process goes through all undelivered, recieved messages, changing the recipent to the sender, adding a note that the account was deleted before the message could be delivered, and follow the sending process
- The user process sends a confirmation to the client, which switches to the login page
- The user process kills itself

## Planning Version 3
We split the plan down into a couple modularized and separate implementations. This will ensure that each portion can be changed with minimal impact on other components, as well increase our ability to remain organized.

### Key Components:
- Database

### Database:
- access everything using SQLite on .db files
- one passwords.db file with username-password pairs (not plaintext passwords, of course)
    - have entries for Username and hashed_password
- one messages.db file with messages
    - have sender, reciever, time sent, delivered, subject, message
- one users.db with usernames and maybe things like # of undelivered messages
- have one process to query the database to prevent issues on concurrency
- have a database class with the necessary functions
- make sure that the database class contains \_\_exit\_\_ definitions so the .db doesn't get corrupted
- For processes to communicate with the databse process, create a new pipe for each communication and close it immediately when done to avoid dealing with the semantics of leaving a pipe open and getting inturrupted
    - However, should figure out how to keep the pipe open and figure out the correct error catching, both for efficiency, and also due to the fact that the program would break if an interrupt came in at the moment before the pipe is closed in the current implementation.