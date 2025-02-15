# Wire Protocols: Assignment Specifications
Charlie Chen and Eric Gong

## Creating an account. The user supplies a unique (login) name. If there is already an account with that name, the user is prompted for the password. If the name is not being used, the user is prompted to supply a password. The password should not be passed as plaintext.
The client is first prompted to supply a username. If the username matches a currently existing username, we request a password, and if the password matches, we proceed with login. Otherwise, we inform the user that no account with the specified username exists, and the client is prompted to define a password to create a new account. The password must be entered twice (so the user doesn't accidentally create an account with a password is different from the password they expected, due to a mistake). 

We hash the password with SHA256, before passing it to the login process, and subsequently, the database process. Thus the password is always passed and stored in its hashed form.

## Log in to an account. Using a login name and password, log into an account. An incorrect login or bad user name should display an error. A successful login should display the number of unread messages.
Once the Client has entered a username and password pair that matches with that of a valid user, we check to see if that user account is already logged in elsewhere. If not, we inform the client that the login is successful, displaying both the number of unread and total messages in the user's inbox. Otherwise, we inform the client that they are already logged in elsewhere.

## List accounts, or a subset of accounts that fit a text wildcard pattern. If there are more accounts than can comfortably be displayed, allow iterating through the accounts.
we implement username querying using SQL wildcard syntax, given that we implement the persistent message storage via SQLlite3. This allows for a variety of powerful filtering techniques supported by the SQL LIKE command. For instance, to retrieve all user accounts starting with the letter a, the client would input "a%" into the search bar. If they wanted all 5-letter usernames ending in the letter s, the could input "____s" into the search bar.

## Send a message to a recipient. If the recipient is logged in, deliver immediately; if not the message should be stored until the recipient logs in and requests to see the message.
When a client sends a message, it is passed to the database process. The database process mantains a record of which users are currently online. If the recipient is on this list, we send an Alert to the recipient, containing the new message, and updating their inbox. In all cases, sent messages are stored in the message database until the message is requested to be deleted by a recipient or the recipient account is deleted (details in sections to follow)

## Read messages. If there are undelivered messages, display those messages. The user should be able to specify the number of messages they want delivered at any single time.
In the user's inbox, we allow the user to specify how many messages they wish to see. We initially display the sender and the subject. Upon the opening of message, if the message was previously un-read, we send a communication to the database, marking the message as read.

## Delete a message or set of messages. Once deleted messages are gone.
We allow the user to select messages they wish to delete. We pass the unique Id identifiers for these messages to the database which then removes them. Only the recipient of a message is able to see the message, and only the recipient of the message is able to delete messages.

## Delete an account. You will need to specify the semantics of deleting an account that contains unread messages.
For unread messages, we redirect the message back to the sender (by changing the recipient field to match the sender), appending a notice that the message was not read before the user was deleted to the subject line. Then we proceed to delete all messages where the recipient field matches the user being deleted (so all read messages, and all messages where the user sent a message to themselves, regardless of read status). Finally we delete the username and hashed-password pair from the database.

## The client should offer a reasonable graphical interface. Connection information may be specified as either a command-line option or in a configuration file.
We use tkinter to design a graphical interface for the client. We choose to use command-line arguments to specify the hostname and portnames needed for the server and client to run.

## You will need to design the wire protocol— what information is sent over the wire. Communication should be done using sockets constructed between the client and server. It should be possible to have multiple clients connected at any time.
All communication between processes is handled through sockets. Multiple clients can connect to the server at any time.

## You should build two implementations— one should use a custom wire protocol; you should strive to make this protocol as efficient as possible. The other should use JSON. You should then measure the size of the information passed between the client and the server, writing up a comparison in your engineering notebook, along with some remarks on what the difference makes to the efficiency and scalability of the service.
We develop and benchmark both a Custom and JSON wire protocol. The details of the benchmarking, and ensuing analysis can be found within the *Documentation.md* file.