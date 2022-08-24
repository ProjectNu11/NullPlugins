import asyncio
from datetime import datetime
from io import BytesIO

import youtube_dl
from PIL import Image
from aiohttp import ClientSession
from loguru import logger
from pydantic import BaseModel

from library import config
from library.image.oneui_mock.elements import (
    Banner,
    Column,
    Header,
    HintBox,
    GeneralBox,
    OneUIMock,
)
from .include import Photo, User, Video, AnimatedGif
from ..var import STATUS_LINK


class Attachments(BaseModel):
    media_keys: list[str] = []


class EntityAnnotation(BaseModel):
    start: int
    end: int
    probability: float
    type: str
    normalized_text: str


class EntityURLExternalImage(BaseModel):
    url: str
    width: int
    height: int


class EntityURLExternal(BaseModel):
    start: int
    end: int
    url: str
    expanded_url: str
    display_url: str
    images: list[EntityURLExternalImage] = []
    status: int
    title: str
    description: str
    unwound_url: str


class EntityURLMedia(BaseModel):
    start: int
    end: int
    url: str
    expanded_url: str
    display_url: str
    media_key: str


class EntityHashtag(BaseModel):
    start: int
    end: int
    tag: str


class Entities(BaseModel):
    annotations: list[EntityAnnotation] = []
    hashtags: list[EntityHashtag] = []
    urls: list[EntityURLMedia | EntityURLExternal] = []


class PublicMetrics(BaseModel):
    retweet_count: int = 0
    reply_count: int = 0
    like_count: int = 0
    quote_count: int = 0


class UnparsedTweet(BaseModel):
    author_id: int
    attachments: Attachments = Attachments()
    text: str
    entities: Entities = Entities()
    id: int
    created_at: datetime
    public_metrics: PublicMetrics = PublicMetrics()
    possibly_sensitive: bool


class ParsedTweet(UnparsedTweet):
    media: list[Photo | Video | AnimatedGif] = []
    user: User
    has_video: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_video = bool(
            list(filter(lambda x: isinstance(x, (Video, AnimatedGif)), self.media))
        )

    async def get_images(self) -> list[bytes]:
        images: list[bytes] = []
        async with ClientSession() as session:
            for media in self.media:
                url = None
                if isinstance(media, Photo):
                    url = media.url
                elif isinstance(media, (Video, AnimatedGif)):
                    url = media.preview_image_url
                if not url:
                    continue
                async with session.get(url, proxy=config.proxy) as resp:
                    images.append(await resp.read())
        return images

    async def get_video_bytes(self) -> tuple[bytes, str]:
        def get_video_info() -> dict | None:
            for media in self.media:
                if not isinstance(media, (Video, AnimatedGif)):
                    continue
                with youtube_dl.YoutubeDL() as ydl:
                    return ydl.extract_info(
                        STATUS_LINK.format(username=self.user.username, id=self.id),
                        download=False,
                    )

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, get_video_info)
        async with ClientSession() as session:
            async with session.get(info["url"], proxy=config.proxy) as resp:
                return await resp.read(), f"{info['display_id']}.{info['ext']}"

    async def compose(self, banner_text: str = "Twitter 预览") -> bytes:
        logger.info(f"取得推文 {self.id} 图片中...")
        images: list[bytes] = await self.get_images()
        images: list[Image.Image] = [Image.open(BytesIO(image)) for image in images]
        avatar: Image.Image = Image.open(BytesIO(await self.user.get_avatar()))

        def __compose() -> bytes:
            column = Column(
                Banner(banner_text),
                Header(
                    text=self.user.name, description=self.user.username, icon=avatar
                ),
            )

            if self.possibly_sensitive:
                column.add(HintBox("可能包含敏感内容", "本推文可能包含不适合在工作场合查看的内容"))

            column.add(*images)

            box = GeneralBox(text="正文", description=self.text, highlight=True)
            box.add(text="私人推特", description="推特是否对外不可见", switch=self.user.protected)
            column.add(box)

            if hashtags := self.entities.hashtags:
                column.add(
                    GeneralBox(
                        text="标签",
                        description=" ".join(
                            [f"#{hashtag.tag}" for hashtag in hashtags]
                        ),
                    )
                )

            if urls := self.entities.urls:
                external_urls: list[EntityURLExternal] = []
                for url in urls:
                    if not isinstance(url, EntityURLExternal):
                        continue
                    external_urls.append(url)
                if external_urls:
                    for index, url in enumerate(external_urls):
                        box = GeneralBox()
                        box.add(text=f"外部链接 #{index + 1}", description=url.expanded_url)
                        box.add(
                            text="标题",
                            description=url.title,
                        )
                        box.add(
                            text="描述",
                            description=url.description,
                        )
                        column.add(box)

            box = GeneralBox(
                text="转推", description=str(self.public_metrics.retweet_count)
            )
            box.add(text="回复", description=str(self.public_metrics.reply_count))
            box.add(text="点赞", description=str(self.public_metrics.like_count))
            box.add(text="引用", description=str(self.public_metrics.quote_count))
            column.add(box)

            box = GeneralBox(
                text="发布时间", description=self.created_at.strftime("%Y-%m-%d %H:%M:%S")
            )
            box.add(
                text="制图时间", description=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            column.add(box)
            return OneUIMock(column).render_bytes()

        logger.info(f"渲染推文 {self.id} 中...")
        return await asyncio.to_thread(__compose)
