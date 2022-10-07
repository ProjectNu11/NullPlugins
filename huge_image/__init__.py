import random
import sys

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import (
    GroupMessage,
    FriendMessage,
    MessageEvent,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Xml
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexMatch,
    ElementMatch,
    ElementResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import prefix_match
from library.depend import Switch, FunctionCall, Blacklist

saya = Saya.current()
channel = Channel.current()

channel.name("HugeImage")
channel.author("nullqwertyuiop")
channel.description("好大的图")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    prefix_match(),
                    FullMatch("好大的图"),
                    RegexMatch(r"[\n\r]?", optional=True),
                    ElementMatch(Image) @ "image",
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
async def huge_image(
    app: Ariadne,
    event: MessageEvent,
    image: ElementResult,
):
    if image.matched:
        assert isinstance(image.result, Image)
        suffix = image.result.id.split(".")[-1]
        img_id = image.result.id.split(".")[0][1:-1].replace("-", "")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"https://gchat.qpic.cn/gchatpic_new/0/1-1-{img_id}/0"
            ) as resp:
                filesize = sys.getsizeof(await resp.read())
        xml = (
            f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"
            f'<msg serviceID="5" templateID="1" action="" '
            f'brief="[图片表情]" sourceMsgId="0" url="" '
            f'flag="0" adverSign="0" multiMsgFlag="0">'
            f'<item layout="0" advertiser_id="0" aid="0">'
            f'<image uuid="{img_id}.{suffix}" md5="{img_id}" '
            f'GroupFiledid="{int(random.random() * 1_000_000_000)}" '
            f'filesize="{filesize}" '
            f'local_path="/storage/emulated/0/Android/data/'
            f"com.tencent.mobileqq/Tencent/MobileQQ/chatpic/chatimg/"
            f'aa3/Cache_{img_id}" minWidth="400" minHeight="400" '
            f'maxWidth="400" maxHeight="400" />'
            f'</item><source name="" icon="" action="" appid="-1" /></msg>'
        )
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Xml(xml=xml)),
        )
