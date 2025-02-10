from Modules.DataObjects import DataObject, MessageObject, byte_decode, byte_encode
from Modules.Flags import EncodeType

def tests():
    
    print(byte_encode((("hi").encode("utf-8"))))
    print(byte_encode((("hi\n").encode("utf-8"))))
    print(byte_encode((("hi\n你好").encode("utf-8"))))
    print(byte_decode(byte_encode((("hi\n你好").encode("utf-8")))))
    print(byte_encode(byte_encode(b"h\ni") + b"\n" + byte_encode(("你\n好").encode("utf-8"))).decode("utf-8"))
    print(byte_decode(byte_encode(byte_encode(b"h\ni") + b"\n" + byte_encode(("你\n好").encode("utf-8")))).decode("utf-8"))

    t = DataObject(datalen = 2, data = ["hello\nhello\n100%\n\n", "你好\n"])
    print(t.to_string())
    t2 = DataObject()
    print(t2.to_string())
    t2.deserialize(t.serialize())
    print(t2.to_string())

    u = DataObject(encode_type=EncodeType.JSON)
    print(u.serialize())

    tjson = DataObject(encode_type=EncodeType.JSON, datalen = 2, data = ["hello\nhello\n100%\n\n", "你好\n"])
    print(tjson.serialize())

    print("Test cross-method deserialization")
    t2.deserialize(tjson.serialize())
    print(t2.to_string())
    u.deserialize(t.serialize())
    print(u.to_string())

    mt = MessageObject(sender="Me", recipient="You", time="Today", subject="test")
    print(mt.to_string())
    mt2 = MessageObject(sender="Me", recipient="You")
    print(mt2.to_string())
    mt2.deserialize(mt.serialize())
    print(mt2.to_string())

    mu = MessageObject(encode_type=EncodeType.JSON, sender="Me", recipient="You")
    print(mu.serialize())

    mtjson = MessageObject(encode_type=EncodeType.JSON, sender="Me", recipient="You", time="Today", subject="test")
    print(mtjson.serialize())

    print("Test cross-method deserialization")
    mt2.deserialize(mtjson.serialize())
    print(mt2.to_string())
    mu.deserialize(mt.serialize())
    print(mu.to_string())