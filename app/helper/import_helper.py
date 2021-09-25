import json
import os
from http.client import HTTPException
from typing import List

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import DATASET_DIR
from app.models import models
from app.models.crud import get_artist, get_user_by_name, get_track, count_playlist_entries, create_user, create_artist, \
    create_track, create_playlist_entry, bulk_create, exists_artist, exists_track
from app.models.schemas import Artist, User, Track, Playlist


class FileReader:
    db: Session
    artist_msids = set()
    artists: List[models.Artist] = []
    track_msids = set()
    tracks: List[models.Track] = []
    user_id: int
    users: List[models.User] = []
    user_names = set()
    playlist_id: int
    playlist_entries: List[models.Playlist] = []
    file_path: str = os.path.join(DATASET_DIR, "dataset.txt")
    first_new_user = True

    def __init__(self, db: Session):
        self.db = db
        self.user_id = int(db.query(models.User).count() + 1)
        self.playlist_id = int(count_playlist_entries(db=db) + 1)

    def get_no_lines(self):
        return sum(1 for line in open(self.file_path))

    def read_file_from_to(self, start: int, end: int):
        line_numbers = list(range(start,end))
        with open(self.file_path, 'r', encoding='UTF-8') as file:
            for i, line in enumerate(file):
                if i in line_numbers:
                    self.line_file_import(line)
                elif i > end:
                   break

    def line_file_import(self, line:str):
        data = json.loads(line)
        artist_msid: str = str(data['track_metadata']['additional_info']['artist_msid'])
        artist_name: str = str(data['track_metadata']['artist_name'])
        if artist_msid not in self.artist_msids:
            exists: bool = exists_artist(db=self.db, artist_id=artist_msid)
            if not exists:
                self.artists.append(models.Artist(msid=artist_msid, name=artist_name))
            self.artist_msids.add(artist_msid)

        track_msid: str = str(data['recording_msid'])
        track_name: str = str(data['track_metadata']['track_name'])
        release_name: str = str(data['track_metadata']['release_name'])

        if track_msid not in self.track_msids:
            exists: bool = exists_track(db=self.db, track_id=track_msid)
            if not exists:
                self.tracks.append(models.Track(msid=track_msid, name=track_name, release_name=release_name,
                                           artist_id=artist_msid))
            self.track_msids.add(track_msid)

        user_name: str = str(data['user_name'])
        user: models.User = None
        new_user: bool = False
        if user_name not in self.user_names:
            user: models.User = get_user_by_name(db=self.db, name=user_name)
            if not user:
                if not self.first_new_user:
                    self.user_id += 1
                self.users.append(models.User(id=self.user_id, name=user_name))
                self.user_names.add(user_name)
                self.first_new_user = False

        listened_at: int = int(data['listened_at'])
        playlist_track_id: str = track_msid
        playlist_user_id: int = user.id if user else self.user_id
        self.playlist_entries.append(
            models.Playlist(id=self.playlist_id, listened_at=listened_at, user_id=playlist_user_id,
                            track_id=playlist_track_id))

        self.playlist_id += 1


def bulk_import_from_file(db: Session):
    artist_msids = set()
    artists: List[models.Artist] = []
    track_msids = set()
    tracks: List[models.Track] = []
    user_id: int = int(db.query(models.User).count() + 1)
    users: List[models.User] = []
    user_names = set()
    playlist_id: int = int(count_playlist_entries(db=db) + 1)
    playlist_entries: List[models.Playlist] = []
    file_path: str = os.path.join(DATASET_DIR, "dataset.txt")
    if os.path.isfile(file_path):
        # Read from file line by line
        num_lines = sum(1 for line in open(file_path))
        counter = 1
        logger.info(f" LINES: {num_lines}")
        with open(file_path, 'r', encoding='UTF-8') as file:
            while (line := file.readline().rstrip()):
                data = json.loads(line)
                artist_msid: str = str(data['track_metadata']['additional_info']['artist_msid'])
                artist_name: str = str(data['track_metadata']['artist_name'])
                if artist_msid not in artist_msids:
                    exists: bool = exists_artist(db=db, artist_id=artist_msid)
                    if not exists:
                        artists.append(models.Artist(msid=artist_msid, name=artist_name))
                    artist_msids.add(artist_msid)

                track_msid: str = str(data['recording_msid'])
                track_name: str = str(data['track_metadata']['track_name'])
                release_name: str = str(data['track_metadata']['release_name'])

                if track_msid not in track_msids:
                    exists: bool = exists_track(db=db, track_id=track_msid)
                    if not exists:
                        tracks.append(models.Track(msid=track_msid, name=track_name, release_name=release_name,
                                                   artist_id=artist_msid))
                    track_msids.add(track_msid)

                user_name: str = str(data['user_name'])
                user: models.User = None
                if user_name not in user_name:
                    user: models.User = get_user_by_name(db=db, name=user_name)
                    if not user:
                        users.append(models.User(id=user_id, name=user_name))
                        user_names.add(user_name)

                listened_at: int = int(data['listened_at'])
                playlist_track_id: str = track_msid
                playlist_user_id: int = user.id if user else user_id
                playlist_entries.append(
                    models.Playlist(id=playlist_id, listened_at=listened_at, user_id=playlist_user_id,
                                    track_id=playlist_track_id))

                if not user:
                    user_id += 1
                playlist_id += 1
    else:
        raise HTTPException(status_code=500, detail=f"data source file not found!")
    return bulk_create(db=db, users=users, tracks=tracks, artists=artists, playlist_entries=playlist_entries)


def json_import(data: str, db: Session):
    # Find existing entry or form new model data
    # Check for existing entry by id:
    # Artist:
    data = json.loads(data)

    artist_msid: str = str(data['track_metadata']['additional_info']['artist_msid'])
    artist_name: str = str(data['track_metadata']['artist_name'])
    artist: models.Artist = get_artist(db=db, artist_id=artist_msid)
    if not artist:
        artist = create_artist(db=db, artist=Artist(msid=artist_msid, name=artist_name))

    # Track:
    track_msid: str = str(data['recording_msid'])
    track_name: str = str(data['track_metadata']['track_name'])
    release_name: str = str(data['track_metadata']['release_name'])
    track: models.Track = get_track(db=db, track_id=track_msid)
    if not track:
        track = create_track(db=db, track=(
            schema_track := Track(msid=track_msid, name=track_name, release_name=release_name, artist_id=artist_msid)))

    if track not in artist.tracks:
        artist.tracks.append(track)

    # User:
    user_name: str = str(data['user_name'])
    user_id: int = 0
    user: models.User = get_user_by_name(db=db, name=user_name)
    if not user:
        user_id = int(db.query(models.User).count() + 1)
        user = create_user(db=db, user=User(name=user_name, id=user_id))
    else:
        user_id = user.id

    # Playlist-Entry:
    playlist_entry_id: int = int(count_playlist_entries(db=db) + 1)
    listened_at: int = int(data['listened_at'])
    track_id: str = track_msid
    user_id: int = user_id

    playlist_entry: models.Playlist = create_playlist_entry(db=db, playlist_entry=Playlist(id=playlist_entry_id,
                                                                                           listened_at=listened_at,
                                                                                           track_id=track_id,
                                                                                           user_id=user_id))

    # logger.info(f"User {user}")
    # logger.info(f"Artist {artist}")
    # logger.info(f"Track {track}")
    # logger.info(f"Playlist Entry {playlist_entry}")
    return True
