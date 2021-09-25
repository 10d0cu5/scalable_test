from typing import List, Optional

from pydantic import BaseModel

class JSONImportAdditionalInfoModel(BaseModel):
    release_msid: str
    release_mbid: Optional[str] = None
    recording_mbid: Optional[str] = None
    release_group_mbid: Optional[str] = None
    artist_mbids: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    work_mbids: Optional[List[str]] = []
    isrc: Optional[str] = None
    spotify_id: Optional[str] = None
    tracknumber: Optional[str] = None
    track_mbid: Optional[str] = None
    artist_msid: str
    recording_msid: str

class JSONImportMetdadataModel(BaseModel):
    additional_info: JSONImportAdditionalInfoModel
    artist_name: str
    track_name: str
    release_name: str

class JSONImportModel(BaseModel):
    track_metadata: JSONImportMetdadataModel
    listened_at: int
    recording_msid: str
    user_name: str

class JSONImportData(BaseModel):
    import_data: List[JSONImportModel]

class Playlist(BaseModel):
    id: int
    listened_at: int
    track_id: str
    user_id: int

    class Config:
        orm_mode = True

class User(BaseModel):
    id: int
    name: str
    playlist_entry: List[Playlist] = []

    class Config:
        orm_mode = True

class Track(BaseModel):
    msid: str
    name: str
    release_name: str
    artist_id: str
    playlist_entry: List[Playlist] = []

    class Config:
        orm_mode = True


class Artist(BaseModel):
    msid: str
    name: str
    tracks: List[Track] = []

    class Config:
        orm_mode = True
