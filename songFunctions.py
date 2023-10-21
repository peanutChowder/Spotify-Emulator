from distutils.file_util import move_file
from distutils.util import execute
import sqlite3
import time

conn = None
cursor = None

def connect(path):
    '''
    Connet to data base.

    takes in the path address of the database.
    '''
    global conn, cursor

    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute(' PRAGMA foreign_keys=ON; ')
    conn.commit()

    return

def listen(user_uid, song_sid, sessionManager):
    '''
    listen to a song, When a song is selected for listening,
    a listening event is recorded within the current session 
    of the user (if a session has already started for the user)
    or within a new session (if not).  A listening event is recorded
    by either inserting a row to table listen or increasing the listen
    count in this table by 1.

    takes in user.uid of the current user, song.sid of the current song
    and current session.sno(can be None if user not in session).
    '''

    global conn, cursor

    t =  time.localtime()
    t1 = str(time.strftime("%Y-%m-%d %H:%M:%S", t))

    # add new session to database if user not in session
    add_session_query = '''
                        INSERT INTO sessions
                        SELECT :uid, :sno, :start, NULL;
                        '''
    

    # return the last session sno that the user was in
    new_sno_query = '''
                    SELECT sessions.sno
                    FROM sessions
                    WHERE sessions.uid =:uid
                    ORDER BY sessions.sno DESC
                    LIMIT 1;
                    '''

    # create new row in listen
    add_listen_query = '''
                        INSERT INTO listen
                        SELECT :uid, :sno, :sid, 1.0;
                        '''
    
    # check to see if song have been played in session
    check_query = '''
                SELECT *
                FROM listen
                WHERE listen.uid =:uid
                AND listen.sno =:sno
                AND listen.sid =:sid;
                '''
    
    # update listen cnt by increasing it by 1
    update_cnt_query = '''
                        UPDATE listen
                        SET cnt = cnt + 1
                        WHERE listen.uid =:uid
                        AND listen.sno =:sno
                        AND listen.sid =:sid;
                        '''


    # if user not in session, create new session
    if not sessionManager.isSessionStarted():
        sessionManager.startSession()
        session_sno = sessionManager.getSessionNumber()

        # add song to the listen table
        cursor.execute(add_listen_query, {"uid":user_uid, "sno":session_sno, "sid":song_sid})
        conn.commit()
    else:
        # check to see if song is already played during session
        cursor.execute(check_query, {"uid":user_uid, "sno":session_sno, "sid":song_sid})
        if cursor.fetchone() is None:
            # add new row to listen if it is not
            cursor.execute(add_listen_query, {"uid":user_uid, "sno":session_sno, "sid":song_sid})
            conn.commit()
        else:
            # update listen cnt if it is
            cursor.execute(update_cnt_query, {"uid":user_uid, "sno":session_sno, "sid":song_sid})
            conn.commit()

    print("Done\n")

    return

def info(song_sid):
    '''
    shows detail information about song when give song ID.

    takes in song.sid of the desired song for more info.
    '''
    global conn, cursor

    # Query to find the artistis name who perform the given song, the songs ID, Title, and Duration
    info_query1 ='''
                SELECT artists.name, songs.sid, songs.title, songs.duration
                FROM artists, songs, perform
                WHERE songs.sid =?
                AND lower(artists.aid) = lower(perform.aid)
                AND perform.sid = songs.sid;
                '''
    
    # Query to find the playlists the given song is in
    info_query2 ='''
                SELECT playlists.title, playlists.pid
                FROM songs, playlists, plinclude
                WHERE songs.sid =?
                AND plinclude.sid = songs.sid
                AND lower(plinclude.pid) = playlists.pid;
                '''
    
    # Print out the resurt of the first query
    conn.row_factory = sqlite3.Row
    cursor.execute(info_query1, (song_sid,))
    rows = cursor.fetchall()
    print("Song Infomation:")
    for each in rows:
        print(f"| {each[0]} | {each[1]} | {each[2]} | {each[3]} |")
    print("\n")

    # Print out the result of the second query
    print("Playlists Song is in:")
    cursor.execute(info_query2, (song_sid,))
    rows = cursor.fetchall()
    for each in rows:
        print(f"| {each[0]} | {each[1]} |")

    return

def add_song_to_playlist(playlist_title, song_sid, user_uid):
    '''
    add song to an existing playlist, if playlist doesnt 
    exist then create new playlist then add song to it.

    takes in the playlist.title that the user want to add the song to,
    song.sid of the selected song, and user.uid of the current user.
    '''
    global conn, cursor

    # create playlist if it doesn't exist
    add_playlist_query ='''
                        INSERT INTO playlists
                        SELECT :pid, :title, :uid
                        WHERE NOT EXISTS
                                (SELECT 1
                                FROM playlists
                                WHERE lower(playlists.title) =lower(:title));
                        '''

    # return the largest pid
    pid_query = '''
                SELECT playlists.pid
                FROM playlists
                ORDER BY playlists.pid DESC
                LIMIT 1;
                '''
    
    # return the largest sorder
    sorder_query = '''
                    SELECT plinclude.sorder
                    FROM plinclude, playlists
                    WHERE playlists.pid =:pid
                    AND playlists.pid = plinclude.pid
                    ORDER BY plinclude.sorder DESC
                    LIMIT 1;
                    '''
    
    # add song into playlist
    add_song_query ='''
                    INSERT INTO plinclude
                    SELECT :playlist_pid, :song_sid, :plinclude_sorder
                    WHERE NOT EXISTS
                                (SELECT 1
                                FROM plinclude
                                WHERE plinclude.pid =:pid
                                AND plinclude.sid =:sid);

                    '''
    
    # return the playlist pid that match with the playlist title given
    title_pid_query ='''
                    SELECT playlists.pid
                    FROM playlists
                    WHERE lower(playlists.title) =lower(:title);
                    '''
    
    plinclude_sorder = 1


    # find the last pid in playlists and add one to use as new pid, unless there are no playlists in database
    cursor.execute(pid_query)
    if cursor.fetchone() is None:
        playlist_pid = 1
    else:
        cursor.execute(pid_query)
        playlist_pid = cursor.fetchone()[0] + 1
    conn.commit()

    # create the new playlists if it doesn't exist
    cursor.execute(add_playlist_query, {"pid":playlist_pid, "title":playlist_title, "uid":user_uid, "title":playlist_title})
    conn.commit()

    # set the playlist pid to the pid that match with playlist title given
    cursor.execute(title_pid_query, {"title":playlist_title})
    playlist_pid = cursor.fetchone()[0]
    conn.commit()

    # find the last sorder in plinclude and add one to use as new sorder, unless there are no sorder in database
    cursor.execute(sorder_query, {"pid":playlist_pid})
    if cursor.fetchone() is None:
        plinclude_sorder = 1
    else:
        cursor.execute(sorder_query, {"pid":playlist_pid})
        plinclude_sorder = cursor.fetchone()[0] + 1
    conn.commit()

    # add the song to the playlist
    cursor.execute(add_song_query, {"playlist_pid":playlist_pid, "song_sid":song_sid, "plinclude_sorder":plinclude_sorder, "pid":playlist_pid, "sid": song_sid})
    conn.commit()

    print("Done\n")
    return

def add_song(song_title, song_duration, artist_aid):
    '''
    add song to the database if the song and duration are not already in the databsae.
    
    takes in song.title of the new song, and song.duration of the new song.
    '''
    global conn, cursor

    # add the given title and duration to the database with new sid if not already in database
    add_song_query ='''
                    INSERT INTO songs
                    SELECT :sid, :title, :duration
                    WHERE NOT EXISTS
                            (SELECT 1
                            FROM songs
                            WHERE lower(songs.title) =lower(:title)
                            AND songs.duration =:duration);
                    '''

    # return the song sid of the last song sid
    sid_query = '''
                SELECT songs.sid
                FROM songs
                ORDER BY songs.sid DESC
                LIMIT 1;
                '''

    # add the song and artist to the performed table
    add_perform_query = '''
                        INSERT INTO perform
                        SELECT :aid, :sid
                        WHERE NOT EXISTS
                                (SELECT 1
                                FROM perform
                                WHERE lower(perform.aid) = lower(:aid)
                                AND perform.sid = :sid);
                        '''
    

    # find the last sid in songs and add one to use as new sid, unless there are no songs in database
    cursor.execute(sid_query)
    if cursor.fetchone() is None:
        songs_sid = 1
    else:
        cursor.execute(sid_query)
        songs_sid = cursor.fetchone()[0] + 1
    conn.commit()

    # add song to database if the title and duration is not already in the database
    cursor.execute(add_song_query, {"sid":songs_sid, "title":song_title, "duration":song_duration, "title":song_title, "duration":song_duration})
    conn.commit()

    # add new perform row
    cursor.execute(add_perform_query, {"aid":artist_aid, "sid":songs_sid, "aid":artist_aid, "sid":songs_sid})


    return


def find_top(artists_aid):
    '''
    let artists find their top 3 listeners and top 3 playlist
    that contain largest number of their songs.
    
    takes in artists.aid of the current artists.
    '''

    global conn, cursor

    # list the top 3 playlists that contains the most of artists songs
    top_playlist_query = '''
                        SELECT playlists.title, playlists.pid, count(playlists.pid)
                        FROM playlists, artists, perform, plinclude
                        WHERE lower(artists.aid) =lower(:aid)
                        AND artists.aid = perform.aid
                        AND perform.sid = plinclude.sid
                        AND plinclude.pid = playlists.pid
                        GROUP BY playlists.pid
                        ORDER by count(playlists.pid) DESC
                        LIMIT 3;
                        '''

    # select the top 3 users uid that listen to the artists songs the longest
    top_user_query = '''
                    SELECT uid
                    FROM 
                        (select l.uid, p.aid, sum(l.cnt*s.duration)
                        from listen l, songs s, perform p
                        where l.sid=s.sid and s.sid=p.sid
                        group by l.uid, p.aid
                        order by sum(l.cnt*s.duration) DESC)
                    WHERE lower(aid) =lower(:aid)
                    LIMIT 3;
                    '''
    
    # given the uid of a user change it to the name of the user
    uid_to_name_query = '''
                        SELECT users.name
                        FROM users
                        WHERE lower(users.uid) =lower(:uid)
                        '''

    # print out the title, pid and how many songs of the artists it contains
    conn.row_factory = sqlite3.Row
    cursor.execute(top_playlist_query, {"aid":artists_aid})
    rows = cursor.fetchall()
    print("Playlists that include the largest number of your songs:")
    print("| Title | Pid | # of Songs |")
    print("-" * 28)
    for each in rows:
        print(f"| {each[0]} | {each[1]} | {each[2]} |")
    print("\n")
    

    # get the uid of the top 3 listeners
    conn.row_factory = sqlite3.Row
    cursor.execute(top_user_query, {"aid":artists_aid})
    rows = cursor.fetchall()
    print("Users that listen to your songs the longest are:")
    print("-" * 40)
    # converts all the uid to names
    for each in rows:
        user_uid = each[0]
        cursor.execute(uid_to_name_query, {"uid":user_uid})
        print(cursor.fetchone()[0])

    return



# def getSongInfo():
#     duration = ""
    
#     print("*" * 10, "\nAdding a new song\n", "*" * 10)
#     songTitle = input("Enter song title: ")

#     while not duration.isnumeric():
#         duration = input("Enter song duration: ")

#         if not duration.isnumeric():
#             print("Error: Invalid duration, try again.")

#     return songTitle, int(duration) 




# def artistActions(aid: str) -> str:
#     """Main menu for artist actions

#     Args:
#         aid (str): artist id

#     Returns:
#         str: either 'logout' or 'quit' 
#     """
#     global conn, cursor

#     action = artistMenu()

#     if action == 0:
#         title, duration = getSongInfo()
#         add_song(title, duration, aid)
#     elif action == 1:
#         find_top(aid)
#     elif action == 2:
#         return "logout"
#     elif action == 3:
#         return "quit"

# def artistMenu() -> int:
#     """
#     Display main menu and prompt user for action.

#     Args:
#         uid (str): user id

#     Returns
#         int: number representing selected action
#     """
#     action = None
#     while True:
#         print(
#             """
#             Select an action:
#             [0] Add song 
#             [1] Find top fans and playlists
#             [2] Logout
#             [3] Quit
#             """
#         )
#         action = input("Enter action: ")
        
#         if action.isnumeric() and int(action) in range(4):
#             return int(action)
#         else:
#             print("*" * 10, "\nInvalid action selection.\n", "*" * 10)

def userActions(user_uid, song_sid, sessionManager):
    global conn, cursor

    # user menu
    # until user input vaild action
    x = True
    while x:
        print(
                """
                Select an action:
                [0] Listen to Song
                [1] More Infomation
                [2] Add Song to Playlist
                """)

        action_type = input("your action: ")
        # handle different type of user actions
        if action_type == "0":
            listen(user_uid, song_sid, sessionManager)
            x = False
        elif action_type == "1":
            info(song_sid)
            x = False
        elif action_type == "2":
            playlist_title = input("title of the playlist you want to add the song to: ")
            add_song_to_playlist(playlist_title, song_sid, user_uid)
            x = False

    conn.commit()
    return


def artistActions(artist_aid):
    global conn, cursor

    # artist menu
    # until user input vaild action
    x = True
    while x:
        print(
                """
                Select an action:
                [0] Add Song
                [1] Find Top
                [2] Log Out
                [3] Quit
                """)

        action_type = input("Enter action: ")

        # handle different type of user actions
        if action_type == "0":
            song_title = input("Title of your song: ")
            song_duration = int(input("Duration of your song: "))
            add_song(song_title, song_duration, artist_aid)
        elif action_type == "1":
            find_top(artist_aid)
        elif action_type == "2":
            x = False
            y = "logout"
        elif action_type == "3":
            x = False
            y = "quit"

    conn.commit()
    return y

