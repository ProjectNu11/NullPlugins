from datetime import datetime
from io import BytesIO

from PIL import Image
from aiohttp import ClientSession
from loguru import logger
from pydantic import BaseModel, Field

from library import config
from library.image.oneui_mock.elements import (
    GeneralBox,
    QRCodeBox,
    Column,
    Banner,
    Header,
    OneUIMock,
)
from module.youtube_preview.var import VIDEO_LINK


class Thumbnail(BaseModel):
    url: str
    width: int
    height: int


class Thumbnails(BaseModel):
    default: Thumbnail = None
    medium: Thumbnail = None
    high: Thumbnail = None
    standard: Thumbnail = None
    maxres: Thumbnail = None


class Snippet(BaseModel):
    published_at: datetime = Field(..., alias="publishedAt")
    channel_id: str = Field(..., alias="channelId")
    title: str
    description: str
    thumbnails: Thumbnails
    channel_title: str = Field(..., alias="channelTitle")
    tags: list[str] = []
    category_id: str = Field(..., alias="categoryId")
    live_broadcast_content: str = Field(..., alias="liveBroadcastContent")


class ContentDetails(BaseModel):
    duration: str
    dimension: str
    definition: str
    caption: str
    licensed_content: bool = Field(..., alias="licensedContent")
    content_rating: dict = Field(..., alias="contentRating")
    projection: str


class Statistics(BaseModel):
    view_count: str = Field(..., alias="viewCount")
    like_count: str = Field(..., alias="likeCount")
    favorite_count: str = Field(..., alias="favoriteCount")
    comment_count: str = Field(..., alias="commentCount")


class Video(BaseModel):
    kind: str
    etag: str
    id: str
    snippet: Snippet
    content_details: ContentDetails = Field(..., alias="contentDetails")
    statistics: Statistics

    async def get_thumbnail(self) -> Image.Image:
        async with ClientSession() as session:
            if self.snippet.thumbnails.maxres:
                url = self.snippet.thumbnails.maxres.url
            elif self.snippet.thumbnails.high:
                url = self.snippet.thumbnails.high.url
            elif self.snippet.thumbnails.standard:
                url = self.snippet.thumbnails.standard.url
            elif self.snippet.thumbnails.medium:
                url = self.snippet.thumbnails.medium.url
            else:
                url = self.snippet.thumbnails.default.url
            async with session.get(url, proxy=config.proxy) as resp:
                return Image.open(BytesIO(await resp.read()))

    async def get_channel_avatar(self) -> Image.Image:
        pass

    async def compose(self, banner_text: str = "YouTube 预览") -> bytes:
        column = Column(
            Banner(banner_text),
            Header(
                text=self.snippet.channel_title,
                description=self.snippet.channel_id,
                icon=await self.get_channel_avatar(),
            ),
            await self.get_thumbnail(),
            GeneralBox(text="视频标题", description=self.snippet.title).add(
                text="视频描述", description=self.snippet.description, highlight=True
            ),
            QRCodeBox(VIDEO_LINK.format(id=self.id)),
        )

        if hashtags := self.snippet.tags:
            column.add(
                GeneralBox(
                    text="标签",
                    description=" ".join([f"#{hashtag}" for hashtag in hashtags]),
                )
            )

        box = GeneralBox(text="观看数", description=str(self.statistics.view_count))
        box.add(text="点赞数", description=str(self.statistics.like_count))
        box.add(text="评论数", description=str(self.statistics.comment_count))
        column.add(box)

        box = GeneralBox(
            text="发布时间",
            description=self.snippet.published_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        box.add(text="制图时间", description=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        column.add(box)
        logger.info(f"渲染预览 {self.id} 中...")
        return await OneUIMock(column).async_render_bytes()


class PageInfo(BaseModel):
    total_results: int = Field(..., alias="totalResults")
    results_per_page: int = Field(..., alias="resultsPerPage")


class Response(BaseModel):
    kind: str
    etag: str
    items: list[Video]
    page_info: PageInfo = Field(..., alias="pageInfo")
