from Modules.database_manager import DatabaseManager
from Modules.constants import Status

def tests():
    db = DatabaseManager()
    print("Clearing Database")
    print(db.empty_table() == Status.SUCCESS)

    print("Confirm Cleared Database")
    print(db.output() == Status.NOT_FOUND)

    print("Testing Insertion")
    db.insert_user("username", "password")
    print(db.output() == [('username', 'password')])
    db.insert_user("a", "b")
    print(db.output() == [('username', 'password'), ('a', 'b')])

    print("Testing Password Retrieval")
    print(db.get_password("username") == "password")
    print(db.get_password("a") == "b")
    print(db.get_password("c") == Status.NOT_FOUND)
    print(db.get_password("") == Status.INVALID_INPUT)

    print("Testing User Deletion")
    print(db.delete_user("c") == Status.NOT_FOUND)
    print(db.delete_user("") == Status.INVALID_INPUT)
    print(db.delete_user("a") == Status.SUCCESS)
    print(db.get_password("a") == Status.NOT_FOUND)
    print(db.delete_user("a") == Status.NOT_FOUND)




