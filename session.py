import config
import search
import songFunctions
from datetime import datetime

class SessionManager():
    """
    Manages the current session. There is at most one active session at a time.
    """
    def __init__(self, uid, cursor, connection) -> None:
        self.uid = uid
        self.sessionNum = None

        self.cursor = cursor
        self.connection = connection


    def isSessionStarted(self) -> bool:
        """Check if a session is in progress

        Returns:
            bool: is session started
        """
        if self.sessionNum == None:
            return False

        return True

    def getSessionNumber(self) -> int | None:
        return self.sessionNum

    def startSession(self):
        """
        Begin session
        """
        newSessionNum = self.generateSessionNum()
        currDatetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.addNewSession(newSessionNum, currDatetime)
        self.sessionNum = newSessionNum
        config.dispMessage(f"Started session '{newSessionNum}' for user '{self.uid}' at '{currDatetime}'.")

    def endSession(self) -> None:
        """
        Ends current session
        """
        if self.sessionNum is None:
            config.dispMessage(f"Error: No session in progress, cannot end nonexistant session!")
            return

        currDatetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            """
                update sessions
                set end = ?
                where uid = ?
                and sno = ?
            """,
            (currDatetime, self.uid, self.sessionNum)
        )
        self.connection.commit()

        config.dispMessage(f"Ended session '{self.sessionNum}' for user '{self.uid}' at '{currDatetime}'.")
        self.sessionNum = None


    def generateSessionNum(self) -> int:
        """
        Generate unique session number for user

        Returns:
            int: New user unique session number
        """
    
        self.cursor.execute(
            """
                select s.sno
                from sessions s
                where s.uid = ?
                order by s.sno desc
                limit 1
            """,
            (self.uid,)
        )

        contents = self.cursor.fetchall()
        if not contents:
            lastSessionNum = 0
        else:
            lastSessionNum = contents[0][0]
        
        return lastSessionNum + 1



    def addNewSession(self, sno: int, start: str):
        """
        """
        self.cursor.execute(
            """
                insert into sessions (uid, sno, start)
                values(?, ?, ?)
            """,
            (self.uid, sno, start)
        )
        self.connection.commit()

def getAction(uid: str) -> int:
    """
    Display main menu and prompt user for action.

    Args:
        uid (str): user id

    Returns
        int: number representing selected action
    """
    action = None
    while True:
        print(
            """
            Select an action:
            [0] Start a session
            [1] Search for songs and playlists
            [2] Search for artists
            [3] End current session
            [4] Logout
            [5] Quit
            """
        )
        action = input("Enter action: ")
        
        if action.isnumeric() and int(action) in range(6):
            return int(action)
        else:
            config.dispMessage("Invalid action selection.")

def handleFunctionality(uid: str) -> str:
    """Main entry point for handling the song/playlist/artist search functionality.

    Args:
        uid (str): user id
        userType (str): either 'artist' or 'user'

    Returns:
        str: Returns whether program quits or logs out
    """
    global cursor, connection

    cursor = config.cursor
    connection = config.connection

    sessionManager = SessionManager(uid, cursor, connection)

    action = None
    while action != 4 and action != 5:
        action = getAction(uid)

        if action == 0:
            sessionManager.startSession()

        elif action == 1 or action == 2:
            handleSongAction(action, uid, sessionManager)

        elif action == 3:
            sessionManager.endSession()

        else:
            if sessionManager.isSessionStarted():
                sessionManager.endSession()

            if action == 4:
                config.dispMessage("Logging out")
                return "logout"
            else:
                config.dispMessage("Quitting program")
                return "quit"


def handleSongAction(action: int, uid: str, sessionManager: SessionManager) -> None:
    """Handle when user selects a song from search

    Args:
        action (int): represents either searching song/playlists or artists
        userType (str): user id
        sessionManager (SessionManager): class for managing current session
    """
    global connection, cursor

    if action == 1:
        song = search.search(search.querySongsAndPlaylists, search.selectSongOrPlaylist)
    else:
        song = search.search(search.queryArtists, search.selectArtist)

    # User requested to exit to menu if empty tuple returned
    if len(song) == 0:
        return 
    else:
        songFunctions.conn = connection
        songFunctions.cursor = cursor

        songFunctions.userActions(uid, song[0], sessionManager)

    

def main():
    global connection, cursor
    path = "mp1.db"
    config.connect(path)
    connection = config.connection
    cursor = config.cursor

    # startSession("u23")
    handleFunctionality("u23")

    connection.close()

if __name__ == "__main__":
    main()