import traceback
from datetime import datetime
from io import StringIO

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import config
from library.depend import Permission
from library.model import UserPerm
from module.build_image.aworda_text_to_image.text2image import create_image

channel = Channel.current()

channel.name("ExceptionHandler")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(ariadne: Ariadne, event: ExceptionThrowed):
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
    image = await create_image(msg, cut=120)
    if isinstance(event.event, (GroupMessage, FriendMessage)):
        await ariadne.send_message(
            event.event.sender.group
            if isinstance(event.event, GroupMessage)
            else event.event.sender,
            MessageChain(
                [
                    Plain("执行操作时发生以下异常："),
                    Image(data_bytes=image),
                ]
            ),
            quote=event.event.message_chain,
        )
    for owner in config.owners:
        await ariadne.send_friend_message(
            owner,
            MessageChain([Plain("发生异常"), Image(data_bytes=image)]),
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
