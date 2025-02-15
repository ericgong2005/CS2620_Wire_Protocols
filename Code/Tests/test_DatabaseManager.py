'''
File containing tests for the DatabaseManager.

Some assertions are redundant between test functions, but are 
necessary (such as inserting users). The total number of tests 
for each function is included above the function definition.

In total, this script contains 108 Test assertions
'''
from Modules.DatabaseManager import DatabaseManager
from Modules.Flags import Status
from Modules.DataObjects import MessageObject

# 9 Test Assertions
def test_database_username_insertion():
    db = DatabaseManager()
    #Empty the table for consistent tests
    db.empty_table()

    #Test insertion of users
    assert db.insert_user("username", "password") == Status.SUCCESS
    assert db.insert_user("a", "b") == Status.SUCCESS
    assert db.insert_user("username", "password") == Status.MATCH
    assert db.insert_user("username", "pass") == Status.MATCH
    assert db.insert_user("1", "2") == Status.SUCCESS
    assert db.insert_user("qwerty", "uiop") == Status.SUCCESS
    assert db.insert_user("username", "password") == Status.MATCH
    assert db.insert_user("1234", "5678") == Status.SUCCESS
    assert db.insert_user("qwerty", "uiop") == Status.MATCH

    db.empty_table()

    db.close()

# 5 Test Assertions
def test_database_get_passwords():
    db = DatabaseManager()
    #Empty the table for consistent tests
    db.empty_table()

    # Insert some users
    assert db.insert_user("username", "password") == Status.SUCCESS
    assert db.insert_user("a", "b") == Status.SUCCESS
    assert db.insert_user("1", "2") == Status.SUCCESS
    assert db.insert_user("qwerty", "uiop") == Status.SUCCESS
    assert db.insert_user("1234", "5678") == Status.SUCCESS

    # Test get passwords
    assert db.get_password("username") == (Status.MATCH, "password")
    assert db.get_password("a") == (Status.MATCH, "b")
    assert db.get_password("1234") == (Status.MATCH, "5678")
    assert db.get_password("user") == (Status.NO_MATCH, None)
    assert db.get_password("Username") == (Status.NO_MATCH, None)

    db.empty_table()

    db.close()

# 4 Test Assertions
def test_database_get_users():
    db = DatabaseManager()
    #Empty the table for consistent tests
    db.empty_table()

    # Insert some users
    assert db.insert_user("username", "password") == Status.SUCCESS
    assert db.insert_user("a", "b") == Status.SUCCESS
    assert db.insert_user("1", "2") == Status.SUCCESS
    assert db.insert_user("qwerty", "uiop") == Status.SUCCESS
    assert db.insert_user("1234", "5678") == Status.SUCCESS

    # Test get user, with filtering
    status, users = db.get_users("All")
    assert (status, users.sort()) == (Status.SUCCESS, ["username", "a", "1", "qwerty", "1234"].sort())
    status, users = db.get_users("Like", "1")
    assert (status, users) == (Status.SUCCESS, ["1"])
    status, users = db.get_users("Like", r"%1%")
    assert (status, users.sort())== (Status.SUCCESS, ["1", "1234"].sort())
    status, users = db.get_users("Like", "1___")
    assert (status, users) == (Status.SUCCESS, ["1234"])

    db.empty_table()

    db.close()

# 4 Test Assertions
def test_database_delete_user():
    db = DatabaseManager()
    #Empty the table for consistent tests
    db.empty_table()

    # Insert some users
    assert db.insert_user("username", "password") == Status.SUCCESS
    assert db.insert_user("a", "b") == Status.SUCCESS
    assert db.insert_user("1", "2") == Status.SUCCESS
    assert db.insert_user("qwerty", "uiop") == Status.SUCCESS
    assert db.insert_user("1234", "5678") == Status.SUCCESS

    # Test delete user (currently user-only)
    assert db.delete_user("username") == Status.SUCCESS
    status, users = db.get_users("All")
    assert (status, users.sort()) == (Status.SUCCESS, ["a", "1", "qwerty", "1234"].sort())
    assert db.insert_user("username", "password") == Status.SUCCESS
    assert db.insert_user("username", "password") == Status.MATCH

    db.empty_table()

    db.close()

# 54 Test Assertions (via iteration)
def test_database_insert_message():
    db = DatabaseManager()
    #Empty the table for consistent tests
    db.empty_table()

    # Test insert message
    test_values = [
        "Test",
        "123",
        "CS2620",
        "\n",
        "\n\n",
        r"%%",
        "你好",
        "你\n好",
        "你\n%\n好",
        "Tes   t",
        "1 23",
        "CS26\t20",
        "\n \n",
        r"% %",
        "你  好",
        "你\n\t好",
        "你\n%\n%\t好",
        "你\n%0\n%1\t好"
    ]
    for text in test_values:
        message = MessageObject(sender="Me", recipient="you", subject=text, body=text)
        print(db.output())
        status, id = db.insert_message(message)
        assert status == Status.SUCCESS
        assert db.insert_message(message) == (Status.SUCCESS, id + 1)
        assert db.insert_message(message) == (Status.SUCCESS, id + 2)

    db.empty_table()

    db.close()

# 14 Test Assertions
def test_database_read_and_delete_message():
    db = DatabaseManager()
    #Empty the table for consistent tests
    db.empty_table()

    # Insert some messages
    message = MessageObject(sender="Me", recipient="you", subject="Test", body="Body")
    print(db.output())
    status, id = db.insert_message(message)
    assert status == Status.SUCCESS
    assert db.insert_message(message) == (Status.SUCCESS, id + 1)
    assert db.insert_message(message) == (Status.SUCCESS, id + 2)

    # Test getting messages, deleting messages, marking as read
    status, values = db.get_message("you", 0, 10, True)
    assert status == Status.SUCCESS and len(values) == 3
    status, values = db.get_message("you", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 3

    assert db.confirm_read("you", [id,id + 1]) == Status.SUCCESS

    status, values = db.get_message("you", 0, 10, True)
    assert status == Status.SUCCESS and len(values) == 1
    status, values = db.get_message("you", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 3

    assert db.delete_message(id) == Status.SUCCESS

    status, values = db.get_message("you", 0, 10, True)
    assert status == Status.SUCCESS and len(values) == 1
    status, values = db.get_message("you", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 2

    assert db.delete_message(id + 2) == Status.SUCCESS
    
    status, values = db.get_message("you", 0, 10, True)
    assert status == Status.SUCCESS and len(values) == 0
    status, values = db.get_message("you", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 1

    db.empty_table()

    db.close()

# 18 Test Assertions
def test_database_delete_user_with_messages():
    db = DatabaseManager()
    #Empty the table for consistent tests
    db.empty_table()

    # Insert some users
    assert db.insert_user("1", "1") == Status.SUCCESS
    assert db.insert_user("2", "2") == Status.SUCCESS
    assert db.insert_user("3", "3") == Status.SUCCESS

    # Insert some messages
    message = MessageObject(sender="1", recipient="2", subject="Test", body="Body")
    print(db.output())
    status, id1 = db.insert_message(message)
    assert status == Status.SUCCESS
    assert db.insert_message(message) == (Status.SUCCESS, id1 + 1)
    assert db.insert_message(message) == (Status.SUCCESS, id1 + 2)

    message = MessageObject(sender="2", recipient="3", subject="Test", body="Body")
    print(db.output())
    status, id2 = db.insert_message(message)
    assert status == Status.SUCCESS
    assert db.insert_message(message) == (Status.SUCCESS, id2 + 1)
    assert db.insert_message(message) == (Status.SUCCESS, id2 + 2)

    message = MessageObject(sender="3", recipient="1", subject="Test", body="Body")
    print(db.output())
    status, id3 = db.insert_message(message)
    assert status == Status.SUCCESS
    assert db.insert_message(message) == (Status.SUCCESS, id3 + 1)
    assert db.insert_message(message) == (Status.SUCCESS, id3 + 2)

    # Set some messages as read:
    assert db.confirm_read("2", [id1]) == Status.SUCCESS
    assert db.confirm_read("3", [id2]) == Status.SUCCESS
    assert db.confirm_read("1", [id3]) == Status.SUCCESS

    # Delete some messages
    assert db.delete_message(id1 + 2) == Status.SUCCESS
    status, values = db.get_message("2", 0, 10, True)
    assert status == Status.SUCCESS and len(values) == 1
    status, values = db.get_message("2", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 2

    assert db.delete_message(id2 + 2) == Status.SUCCESS
    status, values = db.get_message("3", 0, 10, True)
    assert status == Status.SUCCESS and len(values) == 1
    status, values = db.get_message("3", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 2

    assert db.delete_message(id3 + 2) == Status.SUCCESS
    status, values = db.get_message("1", 0, 10, True)
    assert status == Status.SUCCESS and len(values) == 1
    status, values = db.get_message("1", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 2

    # Delete a user, and check that unread messages are returned to sender, read messages are gone
    assert db.delete_user("1") == Status.SUCCESS
    status, users = db.get_users("All")
    assert (status, users.sort()) == (Status.SUCCESS, ['2', '3'].sort())
    assert db.insert_user("1", "1") == Status.SUCCESS
    assert db.insert_user("1", "1") == Status.MATCH

    # Check that unread messages are returned to sender
    status, values = db.get_message("3", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 3

    # Check that no delete messages from the initial user remain
    status, values = db.get_message("1", 0, 10, False)
    assert status == Status.SUCCESS and len(values) == 0

    db.empty_table()

    db.close()