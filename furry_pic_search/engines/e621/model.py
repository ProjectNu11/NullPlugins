from datetime import datetime
from typing import Literal

from pydantic import BaseModel, AnyHttpUrl


class FileModel(BaseModel):
    width: int
    height: int
    ext: str
    size: int
    md5: str
    url: str


class ScoreModel(BaseModel):
    up: int
    down: int
    total: int


class TagModel(BaseModel):
    general: list[str]
    species: list[str]
    character: list[str]
    copyright: list[str]
    artist: list[str]


class PostModel(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    file: FileModel
    score: ScoreModel
    tags: TagModel
    rating: Literal["s", "q", "e"]
    sources: list[AnyHttpUrl]
