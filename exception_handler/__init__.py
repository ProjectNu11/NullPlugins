import asyncio
import traceback
from datetime import datetime
from io import StringIO

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from library import config
from library.depend import Permission
from library.model import UserPerm
from module import modules

Saya.current().require(modules.get_module("build_image").pack)
from module.build_image.util import BuildImage, TextUtil

channel = Channel.current()

channel.name("ExceptionHandler")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(ariadne: Ariadne, event: ExceptionThrowed):
    if isinstance(event.event, (GroupMessage, FriendMessage)):
        await ariadne.send_message(
            event.event.sender.group
            if isinstance(event.event, GroupMessage)
            else event.event.sender,
            MessageChain(
                [
                    Plain(f"执行操作时发生以下异常：\n{type(event.exception)}\n"),
                ]
            ),
            quote=event.event.message_chain,
        )
    logger.info("Generating exception image...")
    image = await async_get_image(event)
    logger.info("Sending exception image...")
    for owner in config.owners:
        await ariadne.send_friend_message(
            owner,
            MessageChain(Plain("发生异常"), Image(data_bytes=image)),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[Twilight([FullMatch(".raise")])],
        decorators=[Permission.require(UserPerm.OWNER)],
    )
)
async def exception_raise():
    raise ValueError("异常抛出测试")


def get_image(event: ExceptionThrowed) -> bytes:
    with StringIO() as fp:
        traceback.print_tb(event.exception.__traceback__, file=fp)
        tb = fp.getvalue()
    msg = (
        f"异常时间：\n{datetime.now():%Y年%m月%d日 %H:%M:%S}\n"
        f"异常事件：\n{str(event.event)}\n"
        f"异常类型：\n{type(event.exception)}\n"
        f"异常内容：\n{str(event.exception)}\n"
        f"异常追踪：\n{tb}"
    )
    max_length = 350
    font_size = 15
    font = BuildImage(w=1, h=1, color="white", font_size=font_size).font
    logger.info("Getting exception text box...")
    text_box = TextUtil.get_text_box(msg, font, max_length, check_emoji=False)
    boundary = 20
    image = BuildImage(
        w=text_box[0] + boundary * 2,
        h=int(text_box[1]) + boundary * 2,
        color="white",
        font_size=font_size,
    )
    logger.info("Rendering exception text...")
    image.text(
        (boundary, boundary),
        TextUtil.auto_newline(msg, font, max_length),
        fill="black",
        skip_emoji=True,
    )
    return image.pic2bytes()


async def async_get_image(event: ExceptionThrowed) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_image, event)
