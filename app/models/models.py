from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Artist(Base):
    __tablename__ = "artist"
    msid = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    tracks = relationship("Track", back_populates="artist",
                          cascade="all, delete",
                          passive_deletes=True)


class Track(Base):
    __tablename__ = "track"
    msid = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    release_name = Column(String)
    artist_id = Column(String, ForeignKey("artist.msid", ondelete="CASCADE"))
    artist = relationship("Artist", back_populates="tracks")
    playlist_entry = relationship("Playlist", back_populates="track",
                                  cascade="all, delete",
                                  passive_deletes=True)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    playlist_entry = relationship("Playlist", back_populates="user",
                                  cascade="all, delete",
                                  passive_deletes=True)


class Playlist(Base):
    __tablename__ = "playlist"
    id = Column(Integer, primary_key=True, index=True)
    listened_at = Column(Integer)
    track_id = Column(String, ForeignKey("track.msid", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    track = relationship("Track", back_populates="playlist_entry")
    user = relationship("User", back_populates="playlist_entry")
