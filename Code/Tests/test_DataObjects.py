'''
File containing tests for the DataObjects.

The total number of tests for each function is 
included above the function definition.

Remember to switch the Constants.py encode type to 
test both Custom and Json encodings

In total, if this script is run once on the JSON and
once on the Custom implementation, there are a total of 
218 unique test assertions
'''

from Modules.DataObjects import DataObject, MessageObject, byte_decode, byte_encode
from Modules.Flags import Request, Status, EncodeType
from Modules.Constants import ENCODE_TYPE

# Add the value being checked in a loop to asserts as value == value to ensure the value prints out for failed tests

# 10 Test Assertions (via Iteration)
def test_decode_fail():
    # Check invalid encodings throw exceptions
    test_values = [
        "%",
        r"%a",
        r"%2",
        r"%a%",
        r"%%",
        r"a%%a",
        "This\n",
        r"This%" + "\n", 
        "This\n" + r"%%",
        "\n"
    ]
    for value in test_values:
        failed = False
        try:
            byte_decode(value.encode("utf-8"))
        except:
            failed = True
        assert value == value and failed

# 72 Test Assertions (via Iteration)
def test_single_level_encode_decode():
    # Normal functionality
    test_values = [ # (decoded, encoded)
        ("Test", "Test"),
        ("123", "123"),
        ("CS2620", "CS2620"),
        ("\n", "%1"),
        ("\n\n", r"%1%1"),
        (r"%%", r"%0%0"),
        ("你好", "你好"),
        ("你\n好", "你%1好"),
        ("你\n%\n好", r"你%1%0%1好"),
        ("Tes   t", "Tes   t"),
        ("1 23", "1 23"),
        ("CS26\t20", "CS26\t20"),
        ("\n \n", "%1 %1"),
        (r"% %", r"%0 %0"),
        ("你  好", "你  好"),
        ("你\n\t好", "你%1\t好"),
        ("你\n%\n%\t好", r"你%1%0%1%0" + "\t好"),
        ("你\n%0\n%1\t好", r"你%1%00%1%01" + "\t好")
    ]
    for decoded, encoded in test_values:
        decoded = decoded.encode("utf-8")
        encoded = encoded.encode("utf-8")
        assert encoded == encoded and decoded == decoded and byte_encode(decoded) == encoded
        assert encoded == encoded and decoded == decoded and byte_decode(encoded) == decoded
        assert decoded == decoded and byte_decode(byte_encode(decoded)) == decoded
        assert encoded == encoded and byte_encode(byte_decode(encoded)) == encoded

# 60 Test Assertions (via Iteration)
def test_multi_level_encode_decode():
    # Encoding encodings and decoding decodings
    test_values = [ # decoded, encoded, double encoded, triple encoded
        ("Test", "Test", "Test" , "Test"),
        ("123", "123", "123", "123"),
        ("CS2620", "CS2620", "CS2620", "CS2620"),
        ("\n", "%1", "%01", "%001"),
        ("\n\n", r"%1%1", r"%01%01", r"%001%001"),
        (r"%%", r"%0%0", r"%00%00", r"%000%000"),
        ("你好", "你好", "你好", "你好"),
        ("你\n好", "你%1好", "你%01好", "你%001好"),
        ("你\n%\n好", r"你%1%0%1好", r"你%01%00%01好", r"你%001%000%001好"),
        ("CS26\t20", "CS26\t20", "CS26\t20", "CS26\t20"),
        ("\n \n", "%1 %1", "%01 %01", "%001 %001"),
        ("你\n%\n%\t好", r"你%1%0%1%0" + "\t好", r"你%01%00%01%00" + "\t好", r"你%001%000%001%000" + "\t好")
    ]
    for decoded, encoded, do_encoded, tri_encoded in test_values:
        decoded = decoded.encode("utf-8")
        encoded = encoded.encode("utf-8")
        do_encoded = do_encoded.encode("utf-8")
        tri_encoded = tri_encoded.encode("utf-8")
        assert (encoded == encoded and decoded == decoded and do_encoded == do_encoded and tri_encoded == tri_encoded and 
                byte_encode(byte_encode(decoded)) == do_encoded)
        assert (encoded == encoded and decoded == decoded and do_encoded == do_encoded and tri_encoded == tri_encoded and 
                byte_encode(byte_encode(byte_encode(decoded))) == tri_encoded)
        assert (encoded == encoded and decoded == decoded and do_encoded == do_encoded and tri_encoded == tri_encoded and 
                byte_decode(byte_encode(byte_encode(byte_encode(decoded)))) == do_encoded)
        assert (encoded == encoded and decoded == decoded and do_encoded == do_encoded and tri_encoded == tri_encoded and 
                byte_encode(byte_decode(byte_encode(byte_encode(decoded)))) == do_encoded)
        assert (encoded == encoded and decoded == decoded and do_encoded == do_encoded and tri_encoded == tri_encoded and 
                byte_decode(byte_encode(byte_decode(byte_encode(byte_encode(decoded))))) == encoded)

# 26 Test Assertions (via Iteration)
def test_DataObject_deserialize_fail():
    # Check invalid serializations throw exceptions
    if ENCODE_TYPE == EncodeType.CUSTOM:
        test_values = [
            b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n\n",
            b"\n" + rb"1.0%110%10%1173932" + b"\n" + rb"9611%1%12%1hi%01bye" + b"\n",
            b"\n" + rb"1.0%110%1011739329611%1%12%1hi%01bye" + b"\n"
            b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye%01" + b"\n",
            b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye%1" + b"\n",
            b"\n" + rb"1.0%110%10%11739329611112%1hi%01bye" + b"\n",
            b"\n" + rb"2.0%110%10%11739329611%1%12%1hi%01bye" + b"\n",
            b"\n" + rb"2.1%110%10%11739329611%1%12%1hi%01bye" + b"\n",
            b"\n" + rb"2.1%110%10%11739329611%1%11%1hi%01bye" + b"\n"
        ]
    elif ENCODE_TYPE == EncodeType.JSON:
        test_values = [
            b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}}',
            b'{"version": "2.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}',
            b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 1, "data": ["hi", "bye"]}',
            b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 1, "data": 3}'
        ]
    for value in test_values:
        failed = False
        try:
            d = DataObject(method="serial", serial=value)
        except:
            failed = True
        assert value == value and failed
        failed = False
        try:
            d = DataObject()
            d.update(method="serial", serial=value)
        except:
            failed = True
        assert value == value and failed

# 10 Test Assertions (via Iteration)
def test_get_one():
    if ENCODE_TYPE == EncodeType.CUSTOM:
        test_values = [
            (b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n", 
             b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n", 
             b""),

            ((b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n" + b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n" 
                + b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n"), 
             b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n", 
             b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n" + b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n"),

            (b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n" + b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n", 
             b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n", 
             b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n"),

            (b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n" + b"\n" + rb"1.0%110%10%117393", 
             b"\n" + rb"1.0%110%10%11739329611%1%12%1hi%01bye" + b"\n", 
             b"\n" + rb"1.0%110%10%117393"),

            (b"\n" + rb"1.0%110%10%11739329611%1",
             b"",
             b"\n" + rb"1.0%110%10%11739329611%1"),

            (b"", b"", b"")
        ]
    elif ENCODE_TYPE == EncodeType.JSON:
        test_values = [
            (b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}',
             b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}',
             b""),

            (b'{"version": "1.0", "request": 10, "status": 0, "sequence": 17393300',
             b"",
             b'{"version": "1.0", "request": 10, "status": 0, "sequence": 17393300'),

            ((b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}'+ 
                b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}'),
             b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}',
             b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}'),

            ((b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}'+ 
                b'{"version": "1.0", "request": 10, "status": 0, "sequence": 17393300'),
             b'{"version": "1.0", "request": 10, "status": 0, "sequence": 1739330083, "user": "", "datalen": 2, "data": ["hi", "bye"]}',
             b'{"version": "1.0", "request": 10, "status": 0, "sequence": 17393300'),

            (b"",b"",b"")
        ]
    for start, serial, remaining in test_values:
        assert DataObject.get_one(start) == (serial, remaining)

# 28 Test Assertions between JSON and Custom (via Iteration)
def test_DataObject_serialize_deserialize():
    test_values = [
        DataObject(request=Request.GET_ONLINE_USERS, status=Status.SUCCESS, user="Test"),
        DataObject(request=Request.GET_MESSAGE, status=Status.ERROR, user="Hi", datalen=3, data=["a", "b", "c"]),
        DataObject(request=Request.GET_USERS, status=Status.NO_MATCH, user="A", datalen=1, data = ["All"]),
        DataObject(request=Request.GET_USERS, status=Status.MATCH, user="123", datalen=2, data = ["Like", "test"]),
        DataObject(request=Request.DELETE_USER, status=Status.SUCCESS, user="ff"),
        DataObject(request=Request.CONFIRM_LOGOUT, status=Status.ERROR, user="你好"),
        DataObject(request=Request.CONFIRM_READ, status=Status.SUCCESS, user="2**", datalen=0, data=[])
    ]
    for request in test_values:
        copy = DataObject(method="serial", serial=request.serialize())
        assert copy.serialize() == request.serialize()
        copy = DataObject()
        copy.update(method="serial", serial=request.serialize())
        assert copy.serialize() == request.serialize()

# 12 Test Assertions between JSON and Custom (via Iteration)
def test_MessageObject_serialize_deserialize():
    test_values = [
        MessageObject(sender="Me", recipient="you", subject="Test", body="Body"),
        MessageObject(method="tuple", tuple=(23, 'a', 'a', '2025-02-12T01:51:10+00:00', 0, 'subject', 'message')),
        MessageObject(method="tuple", tuple=(24, 'a', 't', '2025-02-12T02:45:07+00:00', 0, 'test', 'body'))
    ]
    for message in test_values:
        copy = MessageObject(method="serial", serial=message.serialize())
        assert copy.serialize() == message.serialize()
        copy = MessageObject(sender="Hi", recipient="Bye", subject="1", body="2")
        copy.update(method="serial", serial=message.serialize())
        assert copy.serialize() == message.serialize()