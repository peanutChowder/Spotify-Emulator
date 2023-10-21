# Import functions
import sqlite3
import getpass
import time
import sys
import songFunctions
import session, config

# Global variables
connection = None
cursor = None

def connect(path):
    '''
    Connect to data base.

    Takes in the path address of the database.
    '''
    global connection, cursor

    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA foreign_keys=ON; ')
    connection.commit()

    return

def login_screen():
    '''
    User or artist login, if id is valid for both users and artists then ask 
    if they want to login as a user or artist.

    Unregistered users are able to sign up
    '''
    global connection, cursor
    # User Input
    id = input('Please login using a valid id: ')
    id = id.lower()
    pwd = getpass.getpass('Please login using a valid password: ')
    login_id = ''
    # Check if id is in user table
    cursor.execute(
                        'SELECT * FROM users WHERE uid = :uname AND pwd = :pw;',
                        { 'uname': id, 'pw': pwd },
                    )
    users_check = cursor.fetchone()
    # Check if id is in artist table
    cursor.execute(
                        'SELECT * FROM artists WHERE aid = :uname AND pwd = :pw;',
                        { 'uname': id, 'pw': pwd },
                    )
    artists_check = cursor.fetchone()
    # Check if query returns object
    if users_check is not None and artists_check is not None:
        # Check if user input correct option
        while True:
            login_class = input('Do you want to login as a user or as an artist? ') 
            login_class = login_class.lower()
            if login_class == 'user':
                break
            if login_class == 'artist':
                break
            else:
                continue
        login_id = id
    # Valid user
    elif users_check is not None:
        print("Login Successful")
        login_class = 'user'
        login_id = id
    # Valid artist
    elif artists_check is not None:
        print("Login Successful")
        login_class = 'artist'
        login_id = id
    else:
        # Register user
        print(" ")
        print("Unregistered user")
        while True:
            unregistered_uid = input('Please provide a unique uid: ')
            if len(unregistered_uid) <= 4:
                break
            else:
                continue
        unregistered_name = input('Please provide a name: ')
        unregistered_pwd = getpass.getpass('Please provide a password: ')
        # Insert registered data into user table
        data = (unregistered_uid, unregistered_name, unregistered_pwd)
        cursor.execute('INSERT INTO users (uid, name, pwd) VALUES (?,?,?);', data)
        connection.commit()
        print("Signup Successful")
        login_class = 'user'
        login_id = unregistered_uid

    connection.commit()    
    return login_class, login_id

def handleFuctionality(login_class, login_id):
    return

def main(argv):
    global connection, cursor
    path = argv[1]
    connect(path)
    
    # Current Time
    t =  time.localtime()
    t1 = time.strftime("%Y-%m-%d %H:%M:%S", t)
    # Variables
    login_class = ''
    login_id = ''
    status = ''
    action = None
    while True:
        login_class, login_id = login_screen()
        if login_class == 'artist':
            songFunctions.conn = connection
            songFunctions.cursor = cursor
            status = songFunctions.artistActions(login_id)
        elif login_class == 'user':
            config.connection = connection
            config.cursor = cursor
            status = session.handleFunctionality(login_id)

        if status == 'quit':
            break
        if status == 'logout':
            pass
    
    connection.commit()
    connection.close()
    return


if __name__ == "__main__":
    main(sys.argv)

