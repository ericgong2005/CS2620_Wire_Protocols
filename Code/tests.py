from Tests import QueryResponseObject_tests
from Tests import Database_tests

def tests():
    # print("Running Database Tests")
    # Database_tests.tests()

    print("Running QueryObject Tests")
    QueryResponseObject_tests.tests()

if __name__ == "__main__":
    tests()