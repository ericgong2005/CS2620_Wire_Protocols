from Modules.DataObjects import DataObject, MessageObject, byte_decode, byte_encode

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

    t3 = DataObject(method="serial", serial = t2.serialize())
    print(t3.to_string())

    u = DataObject()
    print(u.serialize())

    tjson = DataObject(datalen = 2, data = ["hello\nhello\n100%\n\n", "你好\n"])
    print(tjson.serialize())

    print("Test get_one()")
    data = tjson.serialize()
    print(DataObject.get_one(b""))
    print(DataObject.get_one(data[:8]))
    print(DataObject.get_one(data))
    print(DataObject.get_one(data + data[:8]))
    print(DataObject.get_one(data + data))

    mt = MessageObject(sender="Me", recipient="You", time="Today", subject="test")
    print(mt.to_string())
    mt2 = MessageObject(sender="Me", recipient="You")
    print(mt2.to_string())
    mt2.deserialize(mt.serialize())
    print(mt2.to_string())

    mt3 = MessageObject(method="serial", serial = mt2.serialize())
    print(mt3.to_string())

    mu = MessageObject(sender="Me", recipient="You")
    print(mu.serialize())

    mtjson = MessageObject(sender="Me", recipient="You", time="Today", subject="test")
    print(mtjson.serialize())