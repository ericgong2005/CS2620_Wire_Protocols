from Modules.data_objects import QueryObject, ResponseObject
from Modules.constants import Status, DB

def tests():
    obj = QueryObject(DB.ADD_USER, "Test", 12345, ["Username", "Password"])
    obj2 = QueryObject()
    obj3 = QueryObject()
    
    print("Test QueryObject Initialization")
    print(obj.request == DB.ADD_USER)
    print(obj.data == ["Username", "Password"])
    print(obj2.data == [""])

    print("Test QueryObject Serialization")
    print(obj.serialize() == ("ADD_USER\nTest\n12345\n2\nUsername\nPassword\n").encode("utf-8"))
    print(obj2.serialize() == ("EMPTY\n\n\n1\n\n").encode("utf-8"))

    print("Test QueryObject Deserialization")
    print(obj3.deserialize(obj2.serialize()) == (Status.SUCCESS, b""))
    print(obj2.serialize() == obj3.serialize())
    print(obj2.deserialize(obj.serialize()) == (Status.SUCCESS, b""))
    print(obj2.serialize() == obj.serialize())
    print(obj3.deserialize(("ADD_USER\nTest\n12345\n2\nUsername\nPassword\nADD_USER\n").encode("utf-8")) == (Status.SUCCESS, ("ADD_USER\n").encode("UTF-8")))
    print(obj3.deserialize(("ADD_USER\nTest\n12345\n2\nUsername\nPassword\n\n").encode("utf-8")) == (Status.SUCCESS, ("\n").encode("UTF-8")))
    print(obj3.deserialize(("ADD_USER\nTest\n12345\n2\nUsername\n").encode("utf-8")) == (Status.INCOMPLETE, ("ADD_USER\nTest\n12345\n2\nUsername\n").encode("UTF-8")))
    print(obj3.deserialize(("EMPTY\n\n\n1\n").encode("utf-8")) == (Status.INCOMPLETE, ("EMPTY\n\n\n1\n").encode("UTF-8")))


    obj = ResponseObject(DB.ADD_USER, Status.SUCCESS, ["Username", "Password"])
    obj2 = ResponseObject()
    obj3 = ResponseObject()
    
    print("Test ResponseObject Initialization")
    print(obj.request == DB.ADD_USER)
    print(obj.status == Status.SUCCESS)
    print(obj.data == ["Username", "Password"])
    print(obj2.data == [""])

    print("Test ResponseObject Serialization")
    print(obj.serialize() == ("ADD_USER\nSUCCESS\n2\nUsername\nPassword\n").encode("utf-8"))
    print(obj2.serialize() == ("EMPTY\nFAIL\n1\n\n").encode("utf-8"))

    print("Test ResponseObject Deserialization")
    print(obj3.deserialize(obj2.serialize()) == (Status.SUCCESS, b""))
    print(obj2.serialize() == obj3.serialize())
    print(obj2.deserialize(obj.serialize()) == (Status.SUCCESS, b""))
    print(obj2.serialize() == obj.serialize())
    print(obj2.serialize() == ("ADD_USER\nSUCCESS\n2\nUsername\nPassword\n").encode("utf-8"))
    print(obj3.deserialize(("ADD_USER\nSUCCESS\n2\nUsername\nPassword\nADD_USER\n").encode("utf-8")) == (Status.SUCCESS, ("ADD_USER\n").encode("UTF-8")))
    print(obj3.deserialize(("ADD_USER\nSUCCESS\n2\nUsername\nPassword\n\n").encode("utf-8")) == (Status.SUCCESS, ("\n").encode("UTF-8")))
    print(obj3.deserialize(("ADD_USER\nSUCCESS\n2\nUsername\n").encode("utf-8")) == (Status.INCOMPLETE, ("ADD_USER\nSUCCESS\n2\nUsername\n").encode("UTF-8")))
    print(obj3.deserialize(("EMPTY\nFAIL\n1\n").encode("utf-8")) == (Status.INCOMPLETE, ("EMPTY\nFAIL\n1\n").encode("UTF-8")))
    print(obj3.deserialize(("EMPTY\nFAIL\n1\\").encode("utf-8")) == (Status.FAIL, ("EMPTY\nFAIL\n1\\").encode("UTF-8")))
    _status, remaining = obj3.deserialize(("ADD_USER\nSUCCESS\n2\nUsername\nPassword\nADD_USER\nSUCCESS\n2\nUsername\nPassword\nADD_USER\n").encode("utf-8"))
    print(obj3.deserialize(remaining) == (Status.SUCCESS, ("ADD_USER\n").encode("UTF-8")))



