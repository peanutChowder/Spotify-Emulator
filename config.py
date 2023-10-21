import sqlite3

connection = None
cursor = None

def dispMessage(msg: str):
    print()
    print("*" * 30)
    print(msg)
    print("*" * 30)

def dispHeader(content: str):
    print("-" * 120)
    print(content)
    print("-" * 120)

def connect(path: str) -> None:
    global connection, cursor
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA foreign_keys=ON; ')
    connection.commit()