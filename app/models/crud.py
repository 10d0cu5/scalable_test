from typing import List

from loguru import logger
from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_name(db: Session, name: str):
    return db.query(models.User).filter(models.User.name == name).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.User):
    db_user = models.User(id=user.id, name=user.name)
    try:
        db.add(db_user)
        db.commit()
    except Exception as e:
        db.refresh(db_user)
        db.commit()
    return db_user

def exists_track(db: Session, track_id:str):
    return db.query(db.query(models.Track).filter(models.Track.msid == track_id).exists()).scalar()
    #return db.query(models.Track.query.filter(models.Track.msid == track_id).exists()).scalar()

def get_track(db: Session, track_id: str):
    return db.query(models.Track).filter(models.Track.msid == track_id).first()


def get_tracks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Track).offset(skip).limit(limit).all()


def create_track(db: Session, track: schemas.Track):
    track = models.Track(msid=track.msid, name=track.name, release_name=track.release_name)
    try:
        db.add(track)
        db.commit()
    except Exception as e:
        db.refresh(track)
        db.commit()
    return track

def exists_artist(db: Session, artist_id:str):
    return db.query(db.query(models.Artist).filter(models.Artist.msid == artist_id).exists()).scalar()
    #return db.query(models.Artist.query.filter(models.Artist.msid == artist_id).exists()).scalar()

def get_artist(db: Session, artist_id: str):
    return db.query(models.Artist).filter(models.Artist.msid == artist_id).first()


def get_artists(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Artist).offset(skip).limit(limit).all()


def create_artist(db: Session, artist: schemas.Artist):
    artist = models.Artist(msid=artist.msid, name=artist.name)
    try:
        db.add(artist)
        db.commit()
    except Exception as e:
        db.refresh(artist)
        db.commit()
    return artist


def get_playlist_entry(db: Session, playlist_entry_id: int):
    return db.query(models.Playlist).filter(models.Playlist.id == playlist_entry_id).first()


def count_playlist_entries(db: Session):
    return db.query(models.Playlist).count()


def get_playlist_entries_by_user(db: Session, user_id: int):
    return db.query(models.Playlist).filter(models.Playlist.user_id == user_id).all()


def count_playlist_entries_by_user(db: Session, user_id: int):
    return db.query(models.Playlist).filter(models.Playlist.user_id == user_id).count()


def get_playlist_entries_by_track(db: Session, track_id: str):
    return db.query(models.Playlist).filter(models.Playlist.track_id == track_id).all()


def create_playlist_entry(db: Session, playlist_entry: schemas.Playlist):
    playlist_object = models.Playlist(listened_at=playlist_entry.listened_at)
    playlist_object.user_id = playlist_entry.user_id
    playlist_object.track_id = playlist_entry.track_id
    try:
        db.add(playlist_object)
        db.commit()
    except Exception as e:
        db.refresh(playlist_object)
        db.commit()
    return playlist_object


def bulk_create(db: Session, users: List[models.User], tracks: List[models.Track], artists: List[models.Artist],
                playlist_entries: List[models.Playlist]):
    try:
        db.bulk_save_objects(artists)
        db.bulk_save_objects(tracks)
        db.bulk_save_objects(users)
        db.bulk_save_objects(playlist_entries)
        db.commit()
    except Exception as e:
        logger.error(e)
        return False
    return True
