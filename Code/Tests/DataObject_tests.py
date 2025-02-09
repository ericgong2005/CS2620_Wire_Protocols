from Modules.DataObjects import DataObject

def tests():
    t = DataObject(datalen = 2, data = ["hello\nhello\n100%\n\n", "你好\n"])
    print(t.encode((("hi").encode("utf-8"))))
    print(t.encode((("hi\n").encode("utf-8"))))
    print(t.encode((("hi\n你好").encode("utf-8"))))
    print(t.decode(t.encode((("hi\n你好").encode("utf-8")))))
    print(t.encode(t.encode(b"h\ni") + b"\n" + t.encode(("你\n好").encode("utf-8"))).decode("utf-8"))
    print(t.decode(t.encode(t.encode(b"h\ni") + b"\n" + t.encode(("你\n好").encode("utf-8")))).decode("utf-8"))

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

    print(t2.deserialize(tjson.serialize()))
    print(u.deserialize(t.serialize()))