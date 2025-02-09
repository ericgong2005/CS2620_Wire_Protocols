from Modules.database_manager import QueryObject, ResponseObject
from Modules.constants import Status, DB

def tests():
    obj = QueryObject(DB.ADD_USER, "Test", 12345, ["Username", "Password"])
    obj2 = QueryObject()
    obj3 = QueryObject()
    
    print("Test QueryObject Initialization")
    print(obj.request == DB.ADD_USER)
    print(obj.data == ["Username", "Password"])
    print(obj2.data == [])

    print("Test QueryObject Serialization")
    print(obj.serialize() == ("ADD_USER\nTest\n12345\n2\nUsername\nPassword").encode("utf-8"))
    print(obj2.serialize() == ("EMPTY\n\n\n0\n").encode("utf-8"))

    print("Test QueryObject Deserialization")
    print(obj3.deserialize(obj2.serialize()) == Status.SUCCESS)
    print(obj2.serialize() == obj3.serialize())
    print(obj2.deserialize(obj.serialize()) == Status.SUCCESS)
    print(obj2.serialize() == obj.serialize())

    obj = ResponseObject(DB.ADD_USER, Status.SUCCESS, ["Username", "Password"])
    obj2 = ResponseObject()
    obj3 = ResponseObject()
    
    print("Test ResponseObject Initialization")
    print(obj.request == DB.ADD_USER)
    print(obj.status == Status.SUCCESS)
    print(obj.data == ["Username", "Password"])
    print(obj2.data == [])

    print("Test ResponseObject Serialization")
    print(obj.serialize() == ("ADD_USER\nSUCCESS\n2\nUsername\nPassword").encode("utf-8"))
    print(obj2.serialize() == ("EMPTY\nFAIL\n0\n").encode("utf-8"))

    print("Test ResponseObject Deserialization")
    print(obj3.deserialize(obj2.serialize()) == Status.SUCCESS)
    print(obj2.serialize() == obj3.serialize())
    print(obj2.deserialize(obj.serialize()) == Status.SUCCESS)
    print(obj2.serialize() == obj.serialize())
    print(obj2.serialize() == ("ADD_USER\nSUCCESS\n2\nUsername\nPassword").encode("utf-8"))




