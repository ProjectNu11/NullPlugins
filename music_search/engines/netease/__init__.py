import urllib.parse
from pathlib import Path

from PIL import Image
from graia.ariadne import Ariadne
from graia.ariadne.message.element import MusicShare, MusicShareKind
from graia.saya import Channel
from pydantic import ValidationError

from library import config
from library.image.oneui_mock.elements import (
    Banner,
    GeneralBox,
    Column,
    OneUIMock,
)
from .model import Song
from ..base import BaseSearch

channel = Channel.current()

BASE_URL = (
    "https://netease-cloud-music-iqgexc1bg-nullqwertyuiop.vercel.app"
    "/search?keywords={keywords}&limit=10"
)
JUMP_URL = "https://music.163.com/song?id={id}"
MUSIC_URL = "https://music.163.com/song/media/outer/url?id={id}.mp3"


class NetEaseSearch(BaseSearch):
    engine_name = "网易"

    @classmethod
    async def search(cls, *keywords: str) -> tuple[bytes, list[MusicShare]]:
        keywords = " ".join(keywords)
        keywords = urllib.parse.quote(keywords)

        async with Ariadne.service.client_session.get(
            BASE_URL.format(keywords=keywords), proxy=config.proxy, timeout=10
        ) as response:
            assert response.status == 200, f"服务器返回错误响应代码 {response.status}"
            data = await response.json()

        assert data["code"] == 200, f"服务器返回错误数据代码 {data['result']}"

        result = data["result"]
        songs: list[Song] = []

        assert result["songCount"], "没有搜索到歌曲"

        for song in result["songs"]:
            try:
                songs.append(Song(**song))
            except ValidationError:
                continue
        assert songs, "没有搜索到歌曲"

        shares: list[MusicShare] = []

        for song in songs:
            song_summary = (
                f"{song.name} - {', '.join([artist.name for artist in song.artists])}"
            )
            shares.append(
                MusicShare(
                    kind=MusicShareKind.NeteaseCloudMusic,
                    title=song.name,
                    summary=", ".join([artist.name for artist in song.artists]),
                    jumpUrl=JUMP_URL.format(id=song.id),
                    brief=song_summary,
                    pictureUrl=song.album.artist.img1v1Url,
                    musicUrl=MUSIC_URL.format(id=song.id),
                )
            )

        return await cls.compose(songs), shares

    @staticmethod
    async def compose(songs: list[Song]) -> bytes:
        column = Column(
            Banner(
                "网易云 歌曲搜索",
                icon=Image.open(Path(__file__).parent.parent.parent / "icon.png"),
            ),
            GeneralBox(text="搜索到以下歌曲", description="请在 60 秒内发送序号进行点歌"),
        )

        for index, song in enumerate(songs):
            column.add(
                GeneralBox(
                    text=song.name,
                    description=f"歌手：{', '.join([artist.name for artist in song.artists])}\n"
                    f"专辑：{song.album.name}",
                    name=f"#{index + 1}",
                )
            )

        mock = OneUIMock(column)
        return await mock.async_render_bytes()
