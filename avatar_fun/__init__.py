import asyncio
import sys
from io import BytesIO
from pathlib import Path
from typing import Union

import numpy
from PIL import Image as PillowImage
from aiohttp import ClientResponseError
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain, At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    RegexMatch,
    ElementMatch,
    ElementResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from moviepy.editor import ImageSequenceClip

from library.config import config
from library.depend import Switch

saya = Saya.current()
channel = Channel.current()

channel.name("AvatarFunPic")
channel.author("SAGIRI-kawaii")
channel.description("一个可以生成头像相关趣味图的插件，在群中发送 `[摸|亲|贴|撕|丢|爬|精神支柱|吞] [@目标|目标qq|目标图片]` 即可")

data_dir = Path(config.path.data) / channel.module
data_dir.mkdir(exist_ok=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True) @ "at1",
                    UnionMatch("垃圾探头", "辣鸡探头", "腊鸡探头"),
                    RegexMatch(r"[\n\r]?", optional=True),
                    ElementMatch(Image, optional=True) @ "image",
                    ElementMatch(At, optional=True) @ "at2",
                ]
            )
        ],
        decorators=[Switch.check(channel.module)],
    )
)
async def avatar_fun_one_element(
    app: Ariadne,
    event: MessageEvent,
    at1: ElementResult,
    image: ElementResult,
    at2: ElementResult,
):
    if image.matched:
        assert isinstance(image.result, Image)
        image_bytes = await get_image(image.result)
    elif at1.matched and not at2.matched:
        assert isinstance(at1.result, At)
        image_bytes = await get_image(at1.result.target)
    elif at2.matched:
        assert isinstance(at2.result, At)
        image_bytes = await get_image(at2.result.target)
    else:
        image_bytes = await event.sender.getAvatar()
    if image_bytes:
        await app.sendMessage(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            await trash(image_bytes),
        )


def get_match_element(message: MessageChain) -> list:
    return [
        element
        for element in message.__root__
        if isinstance(element, Image) or isinstance(element, At)
    ]


async def get_image(img: Union[int, Image]) -> bytes:
    if isinstance(img, int):
        async with get_running(Adapter).session.get(
            url=f"https://q1.qlogo.cn/g?b=qq&nk={img}&s=640"
        ) as resp:
            return await resp.read()
    try:
        img_bytes = await img.get_bytes()
    except ClientResponseError:
        img_id = img.id.split(".")[0][1:-1].replace("-", "")
        async with get_running(Adapter).session.get(
            url=f"https://gchat.qpic.cn/gchatpic_new/0/1-1-{img_id}/0"
        ) as resp:
            img_bytes = await resp.read()
    finally:
        return img_bytes


async def trash(image_bytes: bytes) -> MessageChain:
    pos_data = [
        [0, (0, 0)],
        [1, (0, 0)],
        [2, (41, 41)],
        [3, (41, 31)],
        [4, (41, 32)],
        [5, (41, 34)],
        [6, (41, 33)],
        [7, (41, 33)],
        [8, (41, 33)],
        [9, (41, 33)],
        [10, (41, 33)],
        [11, (41, 33)],
        [12, (41, 33)],
        [13, (41, 33)],
        [14, (41, 33)],
        [15, (41, 31)],
        [16, (41, 28)],
        [17, (41, 33)],
        [18, (38, 49)],
        [19, (39, 69)],
        [20, (39, 68)],
        [21, (39, 68)],
        [22, (41, 70)],
        [23, (38, 70)],
        [24, (0, 0)],
    ]
    frames = []
    avatar = PillowImage.open(BytesIO(image_bytes)).convert("RGBA")
    avatar = avatar.resize((77, 77))

    def write_gif() -> bytes:
        file = Path(data_dir / f"trash{hash(image_bytes)}.gif")
        for index, position in pos_data:
            base = PillowImage.open(
                Path(__file__).parent / "assets" / "trash" / f"{index}.png"
            )
            if position != (0, 0):
                bg = PillowImage.new("RGB", base.size, "white")
                bg.paste(avatar, position)
                bg.paste(base, (0, 0), mask=base)
                base = bg
            frames.append(numpy.array(base))
        with ImageSequenceClip(frames, fps=25) as clip:
            clip.write_gif(file)
        with file.open("rb") as f:
            content = f.read()
        file.unlink(missing_ok=True)
        return content

    loop = asyncio.get_event_loop()
    img_bytes = await loop.run_in_executor(None, write_gif)
    return MessageChain.create(Image(data_bytes=img_bytes))
