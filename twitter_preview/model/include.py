from typing import Literal

from aiohttp import ClientSession
from pydantic import BaseModel

from library import config


class AnimatedGif(BaseModel):
    type: Literal["animated_gif"]
    preview_image_url: str
    media_key: str


class Video(BaseModel):
    type: Literal["video"]
    preview_image_url: str
    duration_ms: int
    media_key: str


class Photo(BaseModel):
    url: Literal["photo"]
    type: str
    media_key: str


class User(BaseModel):
    username: str
    profile_image_url: str
    id: int
    protected: bool
    name: str

    async def get_avatar(self) -> bytes:
        async with ClientSession() as session:
            async with session.get(self.profile_image_url, proxy=config.proxy) as resp:
                return await resp.read()


class Includes(BaseModel):
    media: list[Photo | Video | AnimatedGif]
    users: list[User]
