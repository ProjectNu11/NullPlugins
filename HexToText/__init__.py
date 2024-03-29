import re

from graia.ariadne import Ariadne
from graia.ariadne.event.message import (
    GroupMessage,
    FriendMessage,
    MessageEvent,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    FullMatch,
    RegexResult,
    WildcardMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library.depend import Switch, FunctionCall

from graia.ariadne.message.parser.twilight import SpacePolicy
import binascii


channel = Channel.current()


@channel.use(
    ListenerSchema(
        [GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("转"),
                    UnionMatch("文本", "16").space(SpacePolicy.FORCE) @ "type",
                    WildcardMatch().flags(re.S) @ "data",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def Hex_text(
    app: Ariadne, event: MessageEvent, type: RegexResult, data: RegexResult
):
    if type.result.display == "文本":
        text = binascii.unhexlify(data.result.display).decode("gbk")
    else:
        text = binascii.b2a_hex(data.result.display.encode("gbk")).decode()
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(f"{text}"),
    )
