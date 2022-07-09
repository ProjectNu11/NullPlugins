import asyncio

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    RegexResult,
    FullMatch,
    SpacePolicy,
    RegexMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import config
from library.depend import Switch, FunctionCall
from .function import __all__

saya = Saya.current()
channel = Channel.current()

channel.name("AvatarFunPic")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                    UnionMatch(*__all__.keys()) @ "func",
                    RegexMatch(r".+") @ "args",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def meme(app: Ariadne, event: MessageEvent, func: RegexResult, args: RegexResult):
    args: str = args.result.display
    loop = asyncio.get_event_loop()
    try:
        if not (
            composed := await loop.run_in_executor(
                None, __all__[func.result.display], args
            )
        ):
            return
        msg = MessageChain([Image(data_bytes=composed)])
    except AssertionError as err:
        msg = MessageChain(err.args[0])
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        msg,
    )
