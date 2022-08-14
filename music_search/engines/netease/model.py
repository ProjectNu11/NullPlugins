from pydantic import BaseModel


class Artist(BaseModel):
    id: int
    name: str
    img1v1Url: str


class Album(BaseModel):
    id: int
    name: str
    artist: Artist


class Song(BaseModel):
    id: int
    name: str
    artists: list[Artist]
    album: Album
