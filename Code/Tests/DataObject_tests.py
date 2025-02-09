from Modules.DataObjects import DataObject

def tests():
    t = DataObject(datalen = 2, data = ["hello\nhello\n100%\n\n", "你好\n"])
    print(t.encode((("hi").encode("utf-8"))))
    print(t.encode((("hi\n").encode("utf-8"))))
    print(t.encode((("hi\n你好").encode("utf-8"))))
    print(t.decode(t.encode((("hi\n你好").encode("utf-8")))))
    print(t.encode(t.encode(b"h\ni") + b"\n" + t.encode(("你\n好").encode("utf-8"))).decode("utf-8"))
    print(t.decode(t.encode(t.encode(b"h\ni") + b"\n" + t.encode(("你\n好").encode("utf-8")))).decode("utf-8"))

    print(t.serialize())
    t.deserialize(t.serialize())

    u = DataObject()
    print(u.serialize())
    u.deserialize(u.serialize())