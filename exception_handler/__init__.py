import traceback
from datetime import datetime
from io import StringIO

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import config
from module.build_image.util import BuildImage, TextUtil

channel = Channel.current()

channel.name("ExceptionHandler")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(ariadne: Ariadne, event: ExceptionThrowed):
    if isinstance(event.event, ExceptionThrowed):
        return
    with StringIO() as fp:
        traceback.print_tb(event.exception.__traceback__, file=fp)
        tb = fp.getvalue()
    msg = (
        f"异常时间：\n{datetime.now():%Y年%m月%d日 %H:%M:%S}\n \n"
        f"异常事件：\n{str(event.event)}\n \n"
        f"异常类型：\n{type(event.exception)}\n \n"
        f"异常内容：\n{str(event.exception)}\n \n"
        f"异常追踪：\n{tb}"
    )
    max_length = 350
    font = BuildImage(w=1, h=1, color="white", font_size=15).font
    text_box = TextUtil.get_text_box(msg, font, max_length)
    boundary = 25
    image = BuildImage(
        w=text_box[0] + boundary * 2, h=text_box[1] + boundary * 2, color="white"
    )
    await image.atext(
        (boundary, boundary), TextUtil.auto_newline(msg, font, max_length), fill="black"
    )
    if isinstance(event.event, (GroupMessage, FriendMessage)):
        await ariadne.send_group_message(
            event.event.sender.group
            if isinstance(event.event, GroupMessage)
            else event.event.sender,
            MessageChain(Plain("发生异常\n"), Image(data_bytes=image.pic2bytes())),
        )
    for owner in config.owners:
        await ariadne.send_friend_message(
            owner,
            MessageChain(Plain("发生异常\n"), Image(data_bytes=image.pic2bytes())),
        )
