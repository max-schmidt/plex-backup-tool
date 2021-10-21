import sqlite3
from pathlib import Path
from objects.DatabaseObj import DatabaseObj

def ConnectMusicDatabase(db_folder_path: Path, plex_libraryname: str, plex_username: str = "Plex"):
    file_name = plex_username + "_" + plex_libraryname + "_BackupDB.db"
    db_path = db_folder_path / file_name
    try:
        conn = sqlite3.connect(db_path)
    except Exception:
        print("\nCan not connect to backup database file.\n") 
        raise   
    cursor_1 = conn.cursor()
    cursor_2 = conn.cursor()
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS artists (
                    uid int PRIMARY KEY,
                    artist_name text,
                    user_rating real
                )''')
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS albums (
                    uid int PRIMARY KEY,
                    artist_name text,
                    album_name text,
                    date text,
                    user_rating real
                )''')
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS tracks (
                    uid int PRIMARY KEY,
                    artist_name text,
                    album_name text,
                    date text,
                    track_number text,
                    track_name text,
                    user_rating real
                )''')
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS playlists (
                    uid int PRIMARY KEY,
                    title text,
                    summary text,
                    item_list text
                )''')
    return DatabaseObj(conn, cursor_1, cursor_2)

def ConnectRestoreMusicDatabase(db_folder_path: Path, plex_libraryname: str, plex_username: str = "Plex"):
    file_name = plex_username + "_" + plex_libraryname + "_RestoreDB.db"
    db_path = db_folder_path / file_name
    try:
        conn = sqlite3.connect(db_path)
    except Exception:
        print("\nCan not connect to restore database file.\n") 
        raise   
    cursor_1 = conn.cursor()
    cursor_2 = conn.cursor()
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS artists (
                    new_uid int PRIMARY KEY,
                    new_artist_name text,
                    old_uid int,
                    old_artist_name text,
                    old_user_rating real
                )''')
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS albums (
                    new_uid int PRIMARY KEY,
                    new_artist_name text,
                    new_album_name text,
                    new_date text,
                    old_uid int,
                    old_artist_name text,
                    old_album_name text,
                    old_date text,
                    old_user_rating real
                )''')
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS tracks (
                    new_uid int PRIMARY KEY,
                    new_artist_name text,
                    new_album_name text,
                    new_date text,
                    new_track_number text,
                    new_track_name text,
                    old_uid int,
                    old_artist_name text,
                    old_album_name text,
                    old_date text,
                    old_track_number text,
                    old_track_name text,
                    old_user_rating real
                )''')
    cursor_1.execute('''CREATE TABLE IF NOT EXISTS playlists (
                    old_uid int PRIMARY KEY,
                    old_title text,
                    old_summary text,
                    old_item_list text,
                    new_item_list text
                )''')
    return DatabaseObj(conn, cursor_1, cursor_2)

def DisconnectDatabase(db: DatabaseObj):
    db.conn.commit()
    db.conn.close()
