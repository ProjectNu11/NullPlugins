import asyncio
import math
import re
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Union, Tuple

import qrcode
import youtube_dl
from aiohttp import ClientSession
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import ForwardNode, Image, Forward
from graia.ariadne.message.parser.twilight import Twilight, WildcardMatch, RegexMatch
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from pydantic import BaseModel

from library.config import config
from library.depend.function_call import FunctionCall
from library.depend.switch import Switch
from module.build_image.build_image import TextUtil, BuildImage

saya = Saya.current()
channel = Channel.current()

channel.name("TwitterPreview")
channel.author("nullqwertyuiop")
channel.description("")


class TwitterPreviewConfig(BaseModel):
    canvas_width: int = 700
    bearer: str = None


if not config.get_module_config(channel.module):
    config.update_module_config(channel.module, TwitterPreviewConfig())


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    WildcardMatch(),
                    RegexMatch(
                        r"((?:https?://)?(?:www\.)?twitter\.com/[\w\d]+/status/(\d+))|"
                        r"((?:https?://)?(?:www\.)?(t\.co/[a-zA-Z\d_.-]{10}))"
                    ),
                    WildcardMatch(),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
        ],
    )
)
async def get_tweet(app: Ariadne, event: MessageEvent):
    images, media = await TwitterPreview.generate_image(event.message_chain.display)
    if not images:
        return
    if len(images) == 1:
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain([Image(data_bytes=images[0].pic2bytes())]),
        )
    elif fwd_nodes := [
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now() + timedelta(seconds=15) * (index + 1),
            message=MessageChain([Image(data_bytes=image.pic2bytes())]),
        )
        for index, image in enumerate(images)
    ]:
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain([Forward(fwd_nodes)]),
        )
    if media:
        for __media in media:
            data, name = __media
            try:
                await app.upload_file(
                    data=data,
                    target=event.sender.group
                    if isinstance(event, GroupMessage)
                    else event.sender,
                    name=name,
                )
            except RemoteException as err:
                logger.error(err)
                if "upload check_security fail" in str(err):
                    await app.send_message(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        MessageChain("文件未通过安全检查"),
                    )


class TwitterPreview:
    session: Union[ClientSession, None] = None
    short_link_pattern = re.compile(
        r"(?:https?://)?(?:www\.)?(t\.co/[a-zA-Z\d_.-]{10})"
    )
    status_link_pattern = re.compile(
        r"(?:https?://)?(?:www\.)?twitter\.com/\w+/status/(\d+)"
    )

    @classmethod
    def get_session(cls) -> ClientSession:
        if not cls.session:
            cls.session = ClientSession()
        return cls.session

    @staticmethod
    def get_bearer() -> dict:
        assert config.get_module_config(channel.module, "bearer"), "推特 Bearer 未配置"
        return {
            "Authorization": f"Bearer {config.get_module_config(channel.module, 'bearer')}"
        }

    @classmethod
    async def get_status_id(cls, message: str) -> Optional[List[str]]:
        status_links = []
        if short_links := cls.short_link_pattern.findall(message):
            for short_link in short_links:
                if link := await cls.get_status_link(short_link):
                    status_links.append(link)
        if status_ids := cls.status_link_pattern.findall(
            message + " ".join(status_links)
        ):
            return status_ids

    @classmethod
    async def get_status_link(cls, short_link: str) -> Optional[str]:
        if not short_link.startswith("http"):
            short_link = f"https://{short_link}"
        async with cls.get_session().get(
            url=short_link, proxy=config.proxy, verify_ssl=False
        ) as res:
            if cls.status_link_pattern.findall(str(res.url)):
                return str(res.url)

    @classmethod
    async def get_tweet(cls, status_id: str = None) -> Optional[dict]:
        if not status_id or not status_id.isdigit():
            return
        async with cls.get_session().get(
            headers=cls.get_bearer(),
            url=f"https://api.twitter.com/2/tweets?ids={status_id}"
            f"&tweet.fields=text,created_at,public_metrics,entities"
            f"&expansions=attachments.media_keys,author_id"
            f"&media.fields=preview_image_url,duration_ms,type,url"
            f"&user.fields=profile_image_url",
            proxy=config.proxy,
        ) as resp:
            if resp.status != 200:
                return None
            resp = await resp.json()
            if "errors" in resp.keys():
                return None
            return resp

    @classmethod
    async def generate_image(
        cls, text: str
    ) -> Optional[Tuple[List[BuildImage], List[Tuple[bytes, str]]]]:
        if not (status_ids := await cls.get_status_id(text)):
            return
        images = []
        media = []
        for status_id in status_ids:
            if not (tweet := await cls.get_tweet(status_id)):
                continue
            image, __media = await BuildTweet(tweet).compose()
            images.append(image)
            if __media:
                media.append(__media)
        return images, media

    @classmethod
    async def get_bytes(cls, media_url: str) -> Optional[bytes]:
        async with cls.get_session().get(url=media_url, proxy=config.proxy) as response:
            if response.status == 200:
                return await response.read()

    @staticmethod
    def get_media_info(link: str) -> Optional[dict]:
        with youtube_dl.YoutubeDL() as ydl:
            return ydl.extract_info(link, download=False)

    @classmethod
    async def async_get_media_info(cls, link: str) -> Optional[Tuple[bytes, str]]:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, cls.get_media_info, link)
        if media_bytes := await cls.get_bytes(media_url=info["url"]):
            return media_bytes, f"{info['display_id']}.{info['ext']}"


class BuildTweet:
    __grid: int
    __boundary: int
    __canvas_width: int
    __tweet: dict
    __media: Tuple[bytes, str] = None

    def __init__(self, tweet: dict):
        self.__grid = 30
        self.__boundary = 30
        self.__canvas_width = config.get_module_config(channel.module, "canvas_width")
        if self.__canvas_width < 350:
            logger.error("__canvas_width 必须大于 350")
            self.__canvas_width = 350
        self.__tweet = tweet

    def get_text_url_free(self) -> str:
        body = self.__tweet["data"][0]
        text = body["text"]
        if not (entities := body.get("entities", None)):
            return text
        if not (urls := entities.get("urls", None)):
            return text
        for url in urls:
            text = text.replace(url["url"], "").strip()
        return text

    async def build_avatar(self, header_height: int) -> BuildImage:
        size = math.ceil(header_height * 2 / 3)
        if canvas := await TwitterPreview.get_bytes(
            self.__tweet["includes"]["users"][0]["profile_image_url"]
        ):
            canvas = BuildImage(
                size,
                size,
                background=BytesIO(canvas),
            )
        else:
            canvas = BuildImage(
                size,
                size,
                color="white",
            )
        await canvas.acircle_new()
        return canvas

    async def build_name(self, header_height: int) -> BuildImage:
        canvas = BuildImage(
            self.__canvas_width,
            math.ceil(header_height / 3),
            font_size=30,
            color="white",
        )
        await canvas.atext(
            (0, 0),
            TextUtil.text_to_one_line(
                text=self.__tweet["includes"]["users"][0]["name"],
                font=canvas.font,
                max_length=canvas.w - header_height,
            ),
            (0, 0, 0),
        )
        return canvas

    async def compose_header(self) -> BuildImage:
        header_height = 150 - self.__grid
        header = BuildImage(
            self.__canvas_width, header_height, font_size=25, color="white"
        )
        await header.apaste(
            await self.build_avatar(header_height), (self.__boundary, 25), alpha=True
        )
        await header.apaste(
            await self.build_name(header_height), (header_height, 38), alpha=True
        )
        await header.atext(
            (header_height, 85),
            TextUtil.text_to_one_line(
                text=f"@{self.__tweet['includes']['users'][0]['username']}",
                font=header.font,
                max_length=header.w - header_height,
            ),
            (127, 127, 127),
        )
        return header

    async def build_text(self) -> Optional[BuildImage]:
        text = self.get_text_url_free()
        if not text:
            return
        _, height = TextUtil.get_text_box(
            text,
            BuildImage(w=1, h=1, font_size=40, color="white").font,
            self.__canvas_width - self.__boundary * 2,
        )
        text_img = BuildImage(
            w=self.__canvas_width - self.__boundary * 2,
            h=height,
            font_size=40,
            color="white",
        )
        await text_img.atext(
            (0, 0),
            self.get_text_url_free(),
            (0, 0, 0),
        )
        return text_img

    def get_extended_url(
        self, index: int, offset: int, media_type: str
    ) -> Tuple[Union[None, str], int]:
        if media_type not in ("video", "photo"):
            return None, offset
        url = None
        while True:
            try:
                url = self.__tweet["data"][0]["entities"]["urls"][index + offset][
                    "expanded_url"
                ]
                if re.match(
                    rf"(?:https?://)?(?:www\.)?twitter\.com/\w+/status/(\d+)/{media_type}/\d+",
                    url,
                ):
                    break
                offset += 1
            except KeyError:
                break
        return url, offset

    def get_media_urls(
        self,
    ) -> Tuple[Optional[List[Tuple[str, str, Union[None, str]]]], bool]:
        if not (media := self.__tweet["includes"].get("media", None)):
            return [], False
        media_urls = []
        offset = 0
        has_video = False
        for index, media in enumerate(media):
            if media["type"] == "photo":
                media_urls.append(("photo", media["url"], None))
            if media["type"] in ("video", "animated_gif"):
                extended_url, offset = self.get_extended_url(
                    index, offset, "video" if media["type"] == "video" else "photo"
                )
                media_urls.append(
                    (media["type"], media["preview_image_url"], extended_url)
                )
                has_video = True
        return media_urls, has_video

    async def build_media_base(self, url: str) -> BuildImage:
        media = BuildImage(
            w=0, h=0, background=BytesIO(await TwitterPreview.get_bytes(url))
        )
        width = self.__canvas_width - self.__boundary * 2
        height = math.ceil(width / media.w * media.h)
        await media.aresize(w=width, h=height)
        await media.acircle_corner(self.__boundary)
        return media

    async def build_media(self, media_type: str, url: str) -> BuildImage:
        base = await self.build_media_base(url)
        if media_type == "photo":
            return base
        icon = BuildImage(
            w=150,
            h=150,
            is_alpha=True,
            background=Path(
                Path(__file__).parent, "assets", "icon", f"{media_type}.png"
            ),
        )
        await base.apaste(icon, alpha=True, center_type="center")
        return base

    async def compose_media(self) -> Optional[BuildImage]:
        urls, has_video = self.get_media_urls()
        if not urls:
            return
        if has_video:
            self.__media = await TwitterPreview.async_get_media_info(
                f"https://twitter.com/"
                f"{self.__tweet['includes']['users'][0]['username']}"
                f"/status/{self.__tweet['data'][0]['id']}"
            )
        media = [await self.build_media(media_type, url) for media_type, url, _ in urls]
        width = self.__canvas_width - self.__boundary * 2
        height = sum([img.h for img in media] + [self.__grid * (len(media) - 1)])
        canvas = BuildImage(w=width, h=height, color="white")
        _h = 0
        for img in media:
            await canvas.apaste(img, (0, _h), alpha=True)
            _h += self.__grid + img.h
        return canvas

    async def compose_body(self) -> BuildImage:
        text = await self.build_text()
        if not (media := await self.compose_media()):
            return text
        canvas = BuildImage(
            w=self.__canvas_width,
            h=(text.h if text else 0) + self.__grid + media.h,
            color="white",
        )
        if text:
            await canvas.apaste(text, (self.__boundary, 0), alpha=True)
        await canvas.apaste(
            media, (self.__boundary, (text.h if text else 0) + self.__grid), alpha=True
        )
        return canvas

    @staticmethod
    async def build_watermark() -> Optional[BuildImage]:
        watermark = Path(Path(__file__).parent, "assets", "icon", "watermark.png")
        if not watermark.is_file():
            return
        return BuildImage(140, 140, background=watermark)

    @staticmethod
    def get_icons() -> List[BuildImage]:
        return [
            BuildImage(
                w=30,
                h=30,
                background=Path(Path(__file__).parent, "assets", "icon", f"{icon}.png"),
            )
            for icon in ("time", "comment", "retweet", "like")
        ]

    def get_icon_data(self) -> List[str]:
        return [
            (
                datetime.strptime(
                    self.__tweet["data"][0]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                + timedelta(hours=8)
            ).strftime("%H:%M:%S · %Y年%m月%d日"),
            self.__tweet["data"][0]["public_metrics"]["reply_count"],
            self.__tweet["data"][0]["public_metrics"]["retweet_count"],
            self.__tweet["data"][0]["public_metrics"]["like_count"],
        ]

    async def build_icons(self) -> BuildImage:
        grid = 25
        icon_images = self.get_icons()
        icon_data = self.get_icon_data()
        icons_height = sum([i.h for i in icon_images] + [grid * (len(icon_images) - 1)])
        icons = BuildImage(
            self.__canvas_width, icons_height, font_size=25, color="white"
        )
        _h = 0
        for icon, text in zip(icon_images, icon_data):
            await icons.apaste(icon, (self.__boundary, _h), alpha=True)
            await icons.atext(
                (80, _h),
                TextUtil.text_to_one_line(
                    text=str(text),
                    font=icons.font,
                    max_length=self.__canvas_width - 80 - self.__boundary,
                ),
                (127, 127, 127),
            )
            _h += icon.h + grid
        return icons

    async def build_qrcode(self) -> BuildImage:
        qr = qrcode.QRCode(border=0)
        qr.add_data(
            "https://twitter.com/"
            f"{self.__tweet['includes']['users'][0]['username']}"
            f"/status/{self.__tweet['data'][0]['id']}"
        )
        qr.make(fit=True)
        output = BytesIO()
        qr.make_image(fill_color=(127, 127, 127)).save(output)
        return BuildImage(w=140, h=140, background=output)

    def icon_length_check(self) -> bool:
        return BuildImage(
            w=self.__canvas_width - 80 - self.__boundary,
            h=1,
            font_size=25,
            color="white",
        ).check_font_size("00:00:00 · 00年00月00日")

    async def compose_footer(self) -> BuildImage:
        qr = await self.build_qrcode()
        if self.icon_length_check():
            footer = BuildImage(w=self.__canvas_width, h=qr.h, color="white")
            await footer.apaste(
                qr, (math.ceil((self.__canvas_width - qr.w) / 2), 0), alpha=True
            )
            return footer
        footer = await self.build_icons()
        if watermark := await self.build_watermark():
            await footer.apaste(
                watermark,
                (
                    self.__canvas_width - watermark.w - self.__boundary,
                    footer.h - watermark.h,
                ),
                alpha=True,
            )
        qr_x = math.ceil((self.__canvas_width - qr.w) / 2)
        qr_y = footer.h - qr.h
        await footer.apaste(qr, (qr_x, qr_y), alpha=True)
        return footer

    async def compose(self) -> Tuple[BuildImage, Optional[Tuple[bytes, str]]]:
        header = await self.compose_header()
        body = await self.compose_body()
        footer = await self.compose_footer()
        parts = [part for part in (header, body, footer) if part]
        height = sum([p.h for p in parts] + [self.__grid * (len(parts))])
        canvas = BuildImage(
            w=self.__canvas_width,
            h=height,
            color="white",
        )
        _h = 0
        for part in parts:
            await canvas.apaste(part, (0, _h), alpha=True)
            _h += part.h + self.__grid
        return canvas, self.__media
