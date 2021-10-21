import json

from objects.DatabaseObj import DatabaseObj
# import plexapi package for plex connection
try:
    from plexapi.server import PlexServer
    from plexapi.playlist import Playlist
except ImportError:
    print("No python module named 'plexapi' found.")

def ConnectPlex(plex_url: str, plex_token: str, plex_username: str):
    print("\nConnecting to Plex server...")
    try:
        main_plex = PlexServer(plex_url, plex_token)
        main_account = main_plex.myPlexAccount()
        user_account = main_account.user(plex_username)
        user_plex = PlexServer(plex_url, user_account.get_token(main_plex.machineIdentifier))
        return user_plex
    except Exception:
        print("\nCan not connect to Plex server.\n")  
        raise

def ConnectPlexUser(plex_url: str, plex_token: str, plex_username: str):
    print("\nConnecting to Plex server with user profile.")
    try:
        main_plex = PlexServer(plex_url, plex_token)
        main_account = main_plex.myPlexAccount()
        user_account = main_account.user(plex_username)
        user_plex = PlexServer(plex_url, user_account.get_token(main_plex.machineIdentifier))
        print("Plex User Token is: " + user_account.get_token(main_plex.machineIdentifier))
        return user_plex, user_account.get_token(main_plex.machineIdentifier)
    except Exception:
        print("\nCan not connect to Plex server.\n")
        raise

def GetPlexMusicData(user_plex: PlexServer, plex_libraryname:str, db: DatabaseObj):
    print("\nScanning Plex music library:")
    music_library = user_plex.library.section(plex_libraryname)
    print("\nScanning Artists...")
    for plexartist in music_library.searchArtists():
        db.cursor_1.execute("INSERT OR IGNORE INTO artists(uid, artist_name, user_rating) VALUES (?,?,?)", (plexartist.ratingKey, plexartist.title, plexartist.userRating))
        db.cursor_1.execute("UPDATE artists SET artist_name=?, user_rating=? WHERE uid=?", (plexartist.title, plexartist.userRating, plexartist.ratingKey))
    db.conn.commit()
    print("\nScanning Albums...")
    for plexalbum in music_library.searchAlbums():
        db.cursor_1.execute("INSERT OR IGNORE INTO albums(uid, artist_name, album_name, date, user_rating) VALUES (?,?,?,?,?)", (plexalbum.ratingKey, plexalbum.parentTitle, plexalbum.title, plexalbum.originallyAvailableAt, plexalbum.userRating))
        db.cursor_1.execute("UPDATE albums SET artist_name=?, album_name=?, date=?, user_rating=? WHERE uid=?", (plexalbum.parentTitle, plexalbum.title, plexalbum.originallyAvailableAt, plexalbum.userRating, plexalbum.viewCount))
    db.conn.commit()
    print("\nScanning Tracks...")
    for plextrack in music_library.searchTracks():
        track_album_object = music_library.fetchItem(plextrack.parentKey)
        track_date = track_album_object.originallyAvailableAt
        db.cursor_1.execute("INSERT OR IGNORE INTO tracks(uid, artist_name, album_name, date, track_number, track_name, user_rating) VALUES (?,?,?,?,?,?,?)", (plextrack.ratingKey, plextrack.grandparentTitle, plextrack.parentTitle, track_date, plextrack.trackNumber, plextrack.title, plextrack.userRating))
        db.cursor_1.execute("UPDATE tracks SET artist_name=?, album_name=?, date=?, track_number=?, track_name=?, user_rating=? WHERE uid=?", (plextrack.grandparentTitle, plextrack.parentTitle, track_date, plextrack.trackNumber, plextrack.title, plextrack.userRating, plextrack.ratingKey))
    db.conn.commit()
    print("\nScanning Playlists...")
    playlists = music_library.playlists()
    for playlist in playlists:
        item_list = []
        for item in playlist.items():
            item_list.append(item.ratingKey)
        items_string = json.dumps(item_list)
        db.cursor_1.execute("INSERT OR IGNORE INTO playlists(uid, title, summary, item_list) VALUES (?,?,?,?)", (playlist.ratingKey, playlist.title, playlist.summary,  items_string))
        db.cursor_1.execute("UPDATE playlists SET title=?, summary=?, item_list=? WHERE uid=?", (playlist.title, playlist.summary, items_string, playlist.ratingKey))
    db.conn.commit()

def GetNewPlexMusicData(user_plex: PlexServer, plex_libraryname:str, db: DatabaseObj):
    print("\nScanning Plex music library:")
    music_library = user_plex.library.section(plex_libraryname)
    print("\nScanning Artists...\n")
    for plexartist in music_library.searchArtists():
        db.cursor_1.execute("INSERT OR IGNORE INTO artists(new_uid, new_artist_name) VALUES (?,?)", (plexartist.ratingKey, plexartist.title))
        db.cursor_1.execute("UPDATE artists SET new_artist_name=? WHERE new_uid=?", (plexartist.title, plexartist.ratingKey))
    print("\nScanning Albums...")
    for plexalbum in music_library.searchAlbums():
        db.cursor_1.execute("INSERT OR IGNORE INTO albums(new_uid, new_artist_name, new_album_name, new_date) VALUES (?,?,?,?)", (plexalbum.ratingKey, plexalbum.parentTitle, plexalbum.title, plexalbum.originallyAvailableAt))
        db.cursor_1.execute("UPDATE albums SET new_artist_name=?, new_album_name=?, new_date=? WHERE new_uid=?", (plexalbum.parentTitle, plexalbum.title, plexalbum.originallyAvailableAt, plexalbum.ratingKey))
    print("\nScanning Tracks...")
    for plextrack in music_library.searchTracks():
        track_album_uid = plextrack.parentKey
        track_album_object = music_library.fetchItem(track_album_uid)
        track_date = track_album_object.originallyAvailableAt
        db.cursor_1.execute("INSERT OR IGNORE INTO tracks(new_uid, new_artist_name, new_album_name, new_date, new_track_number, new_track_name) VALUES (?,?,?,?,?,?)", (plextrack.ratingKey, plextrack.grandparentTitle, plextrack.parentTitle, track_date, plextrack.trackNumber, plextrack.title))
        db.cursor_1.execute("UPDATE tracks SET new_artist_name=?, new_album_name=?, new_date=?, new_track_number=?, new_track_name=? WHERE new_uid=?", (plextrack.grandparentTitle, plextrack.parentTitle, track_date, plextrack.trackNumber, plextrack.title, plextrack.ratingKey))
    db.conn.commit() # save database

def PushPlexMusicData(user_plex: PlexServer, plex_libraryname:str, db: DatabaseObj):
    print("\nPushing restored data to Plex server...")
    music_library = user_plex.library.section(plex_libraryname)
    
    print("\nPushing Artists...")
    for plexartist in music_library.searchArtists():
        old_user_rating = db.cursor_1.execute("SELECT old_user_rating FROM artists WHERE new_uid=?", (plexartist.ratingKey,)).fetchone()[0]
        if old_user_rating:
            print("Updating " + plexartist.title)
            plexartist.rate(old_user_rating)    

    print("\nPushing Albums...")
    for plexalbum in music_library.searchAlbums():
        old_user_rating = db.cursor_1.execute("SELECT old_user_rating FROM albums WHERE new_uid=?", (plexalbum.ratingKey,)).fetchone()[0]
        if old_user_rating:
            print("Updating " + plexalbum.parentTitle + " - " + plexalbum.title)
            plexalbum.rate(old_user_rating)         
    
    print("\nPushing Tracks...")
    for plextrack in music_library.searchTracks():
        old_user_rating = db.cursor_1.execute("SELECT old_user_rating FROM tracks WHERE new_uid=?", (plextrack.ratingKey,)).fetchone()[0]
        if old_user_rating:
            print("Updating " + plextrack.grandparentTitle + " - " + plextrack.parentTitle + ": " + str(plextrack.trackNumber) + ". " + plextrack.title)
            plextrack.rate(old_user_rating)

    print("\nCreating Playlists...")
    db.cursor_1.execute("SELECT old_title, old_summary, new_item_list FROM playlists")
    for row in db.cursor_1:
        playlist_title, playlist_summary, item_strings = row
        item_list = json.loads(item_strings)
        item_object_list = []
        for item in item_list:
            item_object_list.append(music_library.fetchItem(int(item)))
        print("Creating Playlist: " + playlist_title)
        new_playlist = Playlist.create(user_plex, playlist_title, items=item_object_list)
        if playlist_summary:
            new_playlist.edit(summary=playlist_summary)
