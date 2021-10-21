# Plex Backup Tool for user ratings and playlists

import io, json
from pathlib import Path
# Local
from modules.database import ConnectMusicDatabase, ConnectRestoreMusicDatabase, DisconnectDatabase
from modules.plex import ConnectPlex, ConnectPlexUser, GetNewPlexMusicData, GetPlexMusicData, PushPlexMusicData
from objects.DatabaseObj import DatabaseObj
# import yaml package
try:
    from ruamel.yaml import YAML
except:
    print("\nNo python module named 'ruamel' found.\n")
# import plexapi package
try:
    from plexapi.server import PlexServer
except ImportError:
    print("\nNo python module named 'plexapi' found.\n")

def SyncMusicDatabases(backup_db: DatabaseObj, restore_db: DatabaseObj):
    print("\nSync Artists...")
    restore_db.cursor_1.execute("SELECT new_uid, new_artist_name FROM artists")
    for row in restore_db.cursor_1:
        new_uid, new_artist_name = row
        old_uid, old_artist_name, old_user_rating = backup_db.cursor_1.execute("SELECT uid, artist_name, user_rating FROM artists WHERE artist_name=?", (new_artist_name,)).fetchone()
        restore_db.cursor_2.execute("UPDATE artists SET old_uid=?, old_artist_name=?, old_user_rating=? WHERE new_uid=?", (old_uid, old_artist_name, old_user_rating, new_uid))
    restore_db.conn.commit()    
    print("\nSync Albums...")
    restore_db.cursor_1.execute("SELECT new_uid, new_artist_name, new_album_name, new_date FROM albums")
    for row in restore_db.cursor_1:
        new_uid, new_artist_name, new_album_name, new_date = row
        old_uid, old_artist_name, old_album_name, old_date, old_user_rating = backup_db.cursor_1.execute("SELECT uid, artist_name, album_name, date, user_rating FROM albums WHERE artist_name=? AND album_name=? AND date=?", (new_artist_name, new_album_name, new_date,)).fetchone()       
        restore_db.cursor_2.execute("UPDATE albums SET old_uid=?, old_artist_name=?, old_album_name=?, old_date=?, old_user_rating=? WHERE new_uid=?", (old_uid, old_artist_name, old_album_name, old_date, old_user_rating, new_uid))
    restore_db.conn.commit()
    print("\nSync Tracks...")
    # known problem: tracks on a multi disc album with equal artist, name and track number (if this exists)
    restore_db.cursor_1.execute("SELECT new_uid, new_artist_name, new_album_name, new_date, new_track_number, new_track_name FROM tracks")
    for row in restore_db.cursor_1:
        new_uid, new_artist_name, new_album_name, new_date, new_track_number, new_track_name = row
        old_uid, old_artist_name, old_album_name, old_date, old_track_number, old_track_name, old_user_rating = backup_db.cursor_1.execute("SELECT uid, artist_name, album_name, date, track_number, track_name, user_rating FROM tracks WHERE artist_name=? AND album_name=? AND date=? AND track_number=? AND track_name=?", (new_artist_name, new_album_name, new_date, new_track_number, new_track_name,)).fetchone() 
        restore_db.cursor_2.execute("UPDATE tracks SET old_uid=?, old_artist_name=?, old_album_name=?, old_date=?, old_track_number=?, old_track_name=?, old_user_rating=? WHERE new_uid=?", (old_uid, old_artist_name, old_album_name, old_date, old_track_number, old_track_name, old_user_rating, new_uid))
    restore_db.conn.commit()
    print("\nCopy Playlists...")
    backup_db.cursor_1.execute("SELECT uid, title, summary, item_list FROM playlists")
    for row in backup_db.cursor_1:
        old_uid, old_title, old_summary, old_items_string = row
        old_item_list = json.loads(old_items_string)
        new_item_list = []
        for item in old_item_list:
            new_uid = restore_db.cursor_1.execute("SELECT new_uid FROM tracks WHERE old_uid=?", (item,)).fetchone()[0]
            if new_uid:
                new_item_list.append(new_uid)
        new_items_string = json.dumps(new_item_list)
        restore_db.cursor_1.execute("INSERT OR IGNORE INTO playlists(old_uid, old_title, old_summary, old_item_list, new_item_list) VALUES (?,?,?,?,?)", (old_uid, old_title, old_summary, old_items_string, new_items_string))
        restore_db.cursor_1.execute("UPDATE playlists SET old_title=?, old_summary=?, old_item_list=?, new_item_list=? WHERE old_uid=?", (old_title, old_summary, old_items_string, new_items_string, old_uid))
    restore_db.conn.commit()

# main
print("----------------\nPlex Backup Tool\n----------------")

# TODO: Arguments parser, main Plex user

restore = False

# load yaml config
yaml = YAML(typ="safe")
yaml.default_flow_style = False
with open("config.yaml", "r") as config_file:
    config_yaml = yaml.load(config_file)
db_folder_path = Path(config_yaml["database"]["folder_path"])
Path(db_folder_path).mkdir(parents=True, exist_ok=True)
plex_url = config_yaml["plex"]["plex_url"]
plex_token = config_yaml["plex"]["plex_token"]
plex_libraryname = config_yaml["plex"]["plex_libraryname"]
plex_username = config_yaml["plex"]["plex_username"]
if "plex_user_token" in config_yaml["plex"]: plex_user_token = config_yaml["plex"]["plex_user_token"]
else: plex_user_token = 0

# connect to plex server
if plex_user_token:
    user_plex = PlexServer(plex_url, plex_user_token)
else:
    user_plex, plex_user_token = ConnectPlexUser(plex_url, plex_token, plex_username)
    config_yaml["plex"]["plex_user_token"] = str(plex_user_token)
    with io.open("config.yaml", "w", encoding="utf8") as config_file:
        yaml.dump(config_yaml, config_file)

# backup or restore date
if restore:
    backup_db = ConnectMusicDatabase(db_folder_path, plex_libraryname, plex_username)
    restore_db = ConnectRestoreMusicDatabase(db_folder_path, plex_libraryname, plex_username)
    GetNewPlexMusicData(user_plex, plex_libraryname, restore_db)
    SyncMusicDatabases(backup_db, restore_db)
    PushPlexMusicData(user_plex, plex_libraryname, restore_db)
    DisconnectDatabase(backup_db)
    DisconnectDatabase(restore_db)
else:
    backup_db = ConnectMusicDatabase(db_folder_path, plex_libraryname, plex_username)
    GetPlexMusicData(user_plex, plex_libraryname, backup_db)
    DisconnectDatabase(backup_db)

print("\nDone!")