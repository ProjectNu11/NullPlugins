import asyncio
import json
import re
import time
from io import BytesIO

import aiohttp
from PIL import Image as PillowImage
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, WildcardMatch
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library.depend import Switch, FunctionCall, Blacklist
from library.image.oneui_mock.elements import (
    Banner,
    Column,
    GeneralBox,
    OneUIMock,
)

saya = Saya.current()
channel = Channel.current()

channel.name("BilibiliLinkResolve")
channel.author("nullqwertyuiop")
channel.description("B站链接解析")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    WildcardMatch(),
                    RegexMatch(
                        r"(http:|https:\/\/)?([^.]+\.)?"
                        r"(bilibili\.com\/video\/"
                        r"((BV|bv)[\w\d]{10}|"
                        r"((AV|av)([\d]+))))|"
                        r"(b23\.tv\/[\w\d]+)"
                    ).flags(re.S),
                    WildcardMatch(),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def bilibili_link_resolve_handler(app: Ariadne, event: MessageEvent):
    if msg := await resolve(event.message_chain.display):
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            msg,
        )


async def resolve(message: str) -> None | MessageChain:
    if match := re.findall(
        r"(?:https?://)?(?:[^.]+\.)?bilibili\.com/video/(?:BV|bv)(\w{10})",
        message,
    ):
        bv = f"bv{match[0]}"
        av = bv_to_av(bv)
        info = await get_info(av)
        return await generate_messagechain(info)
    elif match := re.findall(
        r"(?:https?://)?(?:[^.]+\.)?bilibili\.com/video/(?:AV|av)(\d+)",
        message,
    ):
        av = match[0]
        info = await get_info(av)
        return await generate_messagechain(info)
    elif match := re.findall(r"(https?://\)?(?:[^.]+\.)?b23\.tv/\w+)", message):
        match = match[0]
        if not (match.startswith("http")):
            match = f"https://{match}"
        async with aiohttp.ClientSession() as session:
            async with session.get(match) as res:
                if res.status == 200:
                    link = str(res.url)
                    return await resolve(link)


async def get_info(av: int):
    bilibili_video_api_url = f"https://api.bilibili.com/x/web-interface/view?aid={av}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=bilibili_video_api_url) as resp:
            result = (await resp.read()).decode("utf-8")
    result = json.loads(result)
    return result


def bv_to_av(bv: str) -> int:
    table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
    tr = {table[i]: i for i in range(58)}
    s = [11, 10, 3, 8, 4, 6]
    xor = 177451812
    add = 8728348608
    r = sum(tr[bv[s[i]]] * 58**i for i in range(6))
    return (r - add) ^ xor


async def generate_messagechain(info: dict) -> MessageChain:
    data = info["data"]
    img_url = data["pic"]
    async with aiohttp.ClientSession() as session:
        async with session.get(url=img_url) as resp:
            img_content = await resp.read()
    cover = PillowImage.open(BytesIO(img_content))
    return MessageChain(Image(data_bytes=await async_compose(data, cover)))


def compose(data: dict, cover: PillowImage.Image) -> bytes:
    column = Column()

    banner = Banner(
        "B 站链接解析",
    )

    box1 = GeneralBox()
    box1.add(text="标题", description=str(data["title"]))
    box1.add(text="视频类型", description="原创" if data["copyright"] == 1 else "转载")
    box1.add(
        text="投稿时间",
        description=str(
            time.strftime("%Y-%m-%d", time.localtime(int(data["pubdate"])))
        ),
    )
    box1.add(text="视频长度", description=str(sec_format(data["duration"])))
    box1.add(text="UP 主", description=str(data["owner"].get("name", "")))

    box2 = GeneralBox()
    box2.add(text="简介", description=str(data["desc"]))

    box3 = GeneralBox()
    box3.add(text="播放量", description=str(data["stat"].get("view", "")))
    box3.add(text="弹幕量", description=str(data["stat"].get("danmaku", "")))
    box3.add(text="评论量", description=str(data["stat"].get("reply", "")))
    box3.add(text="点赞量", description=str(data["stat"].get("like", "")))
    box3.add(text="投币量", description=str(data["stat"].get("coin", "")))
    box3.add(text="收藏量", description=str(data["stat"].get("favorite", "")))
    box3.add(text="转发量", description=str(data["stat"].get("share", "")))

    box4 = GeneralBox()
    box4.add(text="AV 号", description=str("av" + str(data["aid"])))
    box4.add(text="BV 号", description=str(data["bvid"]))

    column.add(banner, cover, box1, box2, box3, box4)
    mock = OneUIMock(
        column,
    )
    return mock.render_bytes()


async def async_compose(data: dict, cover: PillowImage.Image) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, compose, data, cover)


def sec_format(secs: int) -> str:
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
