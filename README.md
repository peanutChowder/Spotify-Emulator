# Spotify Emulator

Emulate Spotify sessions with this program. The primary function of this program is to deal with SQL queries, integrated with Python.

The program is run as:
`mini_project_1.py <database.db>` where 'database.db' is a local sqlite database file. This database file should contain tables on user, song, playlist information, etc. A sample .db file is provided.

---

# Functionality

The program contains the following core functionality:

- `Login` Users must login as a user. If their user/pw is not found in the .db, then they will be prompted to make a new account.
- `Beginning sessions` Each user can begin a listening session
- `Search for songs/playlists` Each user can search and browse songs/playlists based on query parameters
- `End the current session` 
- `Logout` Self explanatory.
- `Quit` 
