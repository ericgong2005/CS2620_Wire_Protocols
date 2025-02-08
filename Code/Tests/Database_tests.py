from Modules.database_manager import DatabaseManager

def tests():
    db = DatabaseManager()
    print("Inital Database")
    print(db.output())
    print("Clearing Database")
    db.delete_database()
    print("Cleared Database")
    print(db.output())

    print("Testing Insertion")
    db.insert_user("username", "password")
    print(db.output())
