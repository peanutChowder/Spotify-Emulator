import config
from typing import Callable


def addResultOccurrences(resultOccurrences: dict[tuple, int]) -> None:
    """Generates a dictionary from a 'fetchall()' command that keeps track of
    each row's number of repeats

    Args:
        resultOccurrences (dict): tracks each row as a key and its number of repeats as value
    """
    global connection, cursor

    for result in cursor.fetchall():
            if result in resultOccurrences:
                resultOccurrences[result] += 1
            else:
                resultOccurrences[result] = 1

def querySongsAndPlaylists(term: str) -> None:
    """Perform sqlite3 query for songs and playlists that match the given 'term'
    by their title
    
    Args: 
        term (str): term to match songs and playlists with
    """
    cursor.execute(
        """
            select p.pid, p.title, sum(s.duration), "playlist"
            from playlists p
            inner join plinclude pl on pl.pid = p.pid
            inner join songs s on s.sid = pl.sid
            group by p.pid, p.title 
            having p.title like :search_term
            union
            select s.sid, s.title, s.duration, "song"
            from songs s
            where s.title like :search_term
        """, 
        {"search_term": f"%{term}%"}
    )

def queryArtists(term: str) -> None:
    """Perform sqlite3 query search for artists that match 'term'
    either by their name or by their song title
    
    Args:
        term (str): 
    """
    cursor.execute(
        """
            select temp.aid, temp.name, temp.nationality, songCount, "artist"

            from (
                select a.aid, a.name, a.nationality, "artist"
                from artists a
                inner join perform p on p.aid = a.aid
                inner join songs s on s.sid = p.sid
                where a.name like :search_term
                or s.title like :search_term
                group by a.aid
            ) as temp
            left outer join
            (
                select a.aid, count(*) as songCount
                from artists a
                inner join perform p on p.aid = a.aid
                group by a.aid

            ) as temp1
            on temp.aid = temp1.aid
        """,
        {"search_term": f"%{term}%"}
    )


def search(queryFunc: Callable = None, selectionFunc: Callable = None) -> tuple[str | int]:
    """
    Main search function for playlist/song/artist searches.

    Args:
        queryFunc (function): Function for getting sqlite3 queries for either artist or playlist/songs
        selectionFunc (function): Function for displaying query results and allowing user to select either artist or playlist/songs

    Returns:
        tuple: The selected song and its information in tuple format
    """
    global connection, cursor
    cursor = config.cursor
    connection = config.connection

    searchTerms = getSearchTerms()

    resultOccurrences = {}
    for term in searchTerms:
        queryFunc(term)
        addResultOccurrences(resultOccurrences)

    config.dispMessage(f"""Search results for: '{"', '".join(searchTerms)}'""")

    selection = selectionFunc(
        sorted(resultOccurrences, key=resultOccurrences.get, reverse=True)
    )
    
    
    if len(selection) == 0:
        config.dispMessage("Returning to main menu")
        return selection 

    elif selection[-1] == "playlist":
        song = getPlaylistSongs(selection[0])

    elif selection[-1] == "artist":
        song = getArtistSongs(selection[0])
    else:
        song = selection

    return song


def getArtistSongs(aid) -> tuple[str | int]:
    """
    Query for getting all the songs an artist has performed

    Args:
        aid: artist id
    
    Returns:
        tuple: User selected song
    """
    global cursor, connection

    cursor.execute(
        """
        select s.sid, s.title, s.duration, "song"
        from songs s
        inner join perform p on p.sid = s.sid
        where p.aid = ?
        """,
        (aid,)
    )

    return selectSongOrPlaylist(
        cursor.fetchall()
    )


def getPlaylistSongs(pid: int) -> tuple[str | int]:
    """
    Get all the songs in a playlist

    Args:
        pid (int): id of playlist

    Returns:
        tuple: user selected song
    """
    global cursor, connection

    cursor.execute(
        """
        select s.sid, s.title, s.duration, "song"
        from songs s
        inner join plinclude p on p.sid = s.sid
        where p.pid = ?
        """,
        (pid,)
    )

    return selectSongOrPlaylist(
        cursor.fetchall(),
    )

def handleSelection(selection: str, numResults: int, i: int) -> tuple[str, int]:
    """Handles user selection for the search results menu
    User can go to next page, select a song/artist/playlist, exit to main menu 

    Args:
        selection (str): User entered char
        numResults (int): Number of search results
        i (int): iterator

    Returns:
        tuple[str, int]: selection and iterator
    """
    if (selection.isalpha() and selection not in ["n", "m"]) or selection == "": 
            # Keep prompting user for correct input but don't go to next page
            print("Invalid action, try again")
            selection = "n" 

    elif selection == "n":
        if (i + 5 >= numResults):
            print("No more pages to display")
        else:
            i = i + 5

    elif selection.isnumeric() and (int(selection) >= numResults or int(selection) < 0):
        print("Selected listing number does not exist")
        selection = "n"

    return selection, i
        
def selectSongOrPlaylist(results: list) -> tuple[str | int]:
    """Selection menu for song/playlists where user can select a song/playlist

    Args:
        results (list): Search results containing songs/playlists

    Returns:
        tuple[str | int]: The selected song/playlist
    """
    selection = "n"
    i = 0
    while selection == "n":
        config.dispHeader("Listing number\tId\t\tTitle\t\t\t\t\t\tDuration\t\tType")

        # Display 5 songs/playlists at a time
        for j in range(i, i + 5):
            if j >= len(results):
                break
            id, title, duration, type = results[j]
            print(f"[{j}]\t\t{id}\t\t{title:<50}{duration:<10}\t\t{type:<15}")

        # Get user action
        selection = input(f"Select action: Next page [n], exit to menu [m], select [listing number]:")

        # Exit to menu
        if selection == "m":
            return tuple()
        selection, i = handleSelection(selection, len(results), i)
        
    songOrPlaylist = results[int(selection)]
    config.dispMessage(f"Selected {songOrPlaylist[-1]} '{songOrPlaylist[1]}' with id '{songOrPlaylist[0]}'")

    return songOrPlaylist

def selectArtist(results: list) -> tuple[str | int]:
    """Selection menu for user to select artist

    Args:
        results (list): Search results for matching artists

    Returns:
        tuple[str | int]: The selected artist
    """
    selection = "n"
    i = 0
    while selection == "n":
        config.dispHeader("Listing number\tId\t\tName\t\t\tNationality\t\t\tNumber of songs")

        # Display 5 songs/playlists at a time
        for j in range(i, i + 5):
            if j >= len(results):
                break
            id, name, nationality, numSongs, _ = results[j]
            print(f"[{j}]\t\t{id}\t\t{name:<25}{nationality:<30}\t\t{numSongs:<15}")

        # Get user action
        selection = input(f"Select action: Next page [n], exit to menu [m], select [listing number]:")

        # Exit to menu
        if selection == "m":
            return tuple()
        selection, i = handleSelection(selection, len(results), i)
        
    songOrPlaylist = results[int(selection)]
    config.dispMessage(f"Selected {songOrPlaylist[-1]} '{songOrPlaylist[1]}' with id '{songOrPlaylist[0]}'")

    return songOrPlaylist

def getSearchTerms() -> list[str]:    
    """Get the user's search query terms

    Returns:
        list[str]: search terms
    """
    return input("Enter search terms, separated by space:").split()
    

def main():
    global connection, cursor
    path = "mp1.db"
    config.connect(path)
    connection = config.connection
    cursor = config.cursor

    search()

    connection.close()


if __name__ == "__main__":
    main()