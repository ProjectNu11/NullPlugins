import asyncio
import random
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO
from typing import Literal

from PIL import Image
from aiohttp import ClientSession
from graia.saya import Channel
from pydantic import ValidationError

from library import config
from library.image.oneui_mock.elements import (
    Banner,
    GeneralBox,
    is_dark,
    Column,
    OneUIMock,
)
from .model import PostModel
from ..base import BaseSearch

channel = Channel.current()

BASE_URL = "https://e621.net/posts.json?tags=rating:{rating}+{tags}"

RATING_CORD = {"s": "Safe", "q": "Questionable", "e": "Explicit"}
DEFAULT_RATING = "s"

E621_CFG_KEYS = ["username"]
VERSION = "1.0.0"


class E621Search(BaseSearch):
    last_query: datetime = datetime.fromtimestamp(0)

    __name__ = "E621"

    async def get(
        self,
        *tags: str,
        get_random: bool = True,
        rating: Literal["s", "q", "e"] | None = None,
    ) -> bytes:

        assert self.last_query < datetime.now() - timedelta(seconds=5), "查询速率过快"
        self.last_query = datetime.now()

        tags = "+".join(tags).lower()
        tags = urllib.parse.quote(tags, safe="+")

        assert "rating%3As" not in tags, "不被允许的标签：rating:s"
        assert "rating%3Aq" not in tags, "不被允许的标签：rating:q"
        assert "rating%3Ae" not in tags, "不被允许的标签：rating:e"
        assert "rating%3A" not in tags, "不被允许的标签：rating:"

        if rating is None:
            rating = DEFAULT_RATING

        headers = {
            "User-Agent": f"ProjectNu11-E621Module/{VERSION} (queried by {self.get_username()})"
        }

        async with ClientSession(headers=headers) as session:
            async with session.get(
                BASE_URL.format(tags=tags, rating=rating), proxy=config.proxy
            ) as response:
                assert response.status == 200, f"服务器返回错误代码 {response.status}"

                data = await response.json()

            posts: list[PostModel] = []
            for post in data["posts"]:
                try:
                    posts.append(PostModel(**post))
                except ValidationError:
                    continue
            assert posts, "该标签组合下无搜索结果"

            if get_random:
                post = random.choice(posts)
            else:
                post = max(posts, key=lambda x: x.score.total)

            async with session.get(post.file.url, proxy=config.proxy) as response:
                image = Image.open(BytesIO(await response.read()))

        return await self.compose(post, image)

    @staticmethod
    async def compose(post: PostModel, image: Image) -> bytes:
        dark = is_dark()
        column = Column(dark=dark)

        banner = Banner("E621 图片搜索", dark=dark)
        column.add(banner)
        column.add(image)

        box1 = GeneralBox(dark=dark)
        box1.add(text="标签", description=" ".join(post.tags.general))
        if post.tags.artist:
            box1.add(text="作者", description=" ".join(post.tags.artist))
        if post.tags.character:
            box1.add(text="角色", description=" ".join(post.tags.character))
        if post.tags.copyright:
            box1.add(text="版权", description=" ".join(post.tags.copyright))
        column.add(box1)

        box2 = GeneralBox(dark=dark)
        box2.add(text="评分", description=str(post.score.total))
        box2.add(text="上传时间", description=post.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        box2.add(text="评级", description=RATING_CORD[post.rating])
        column.add(box2)

        box3 = GeneralBox(dark=dark)
        if post.sources:
            for index, source in enumerate(post.sources):
                box2.add(text=f"来源 {index + 1}", description=source)
        column.add(box3)

        mock = OneUIMock(column, dark=dark)
        return await mock.async_render_bytes()

    @staticmethod
    def get_username() -> str:
        assert (
            cfg := config.get_module_config(channel.module, "e621"),
            None,
        ) is not None, "无法获取 E621 配置"
        assert (username := cfg.get("username")) is not None, "无法获取 E621 用户名"
        return username
