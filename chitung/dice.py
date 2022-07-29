import random

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, MessageEvent, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
    RegexResult,
    SpacePolicy,
    UnionMatch,
    FullMatch,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.depend import Blacklist, Switch, FunctionCall
from .vars import chitung_prefix
from .utils.depends import FunctionControl

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(chitung_prefix),
                    RegexMatch(r"([Dd](ice)? ?)|(\[Dd])").space(SpacePolicy.NOSPACE),
                    RegexMatch(r"[1-9]\d{0,7}") @ "faces",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionControl.enable("responder"),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_single_dice_handler(
    app: Ariadne, event: MessageEvent, faces: RegexResult
):
    faces = int(faces.result.display)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(f"您掷出的点数是:{random.randint(1, faces)}"),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(chitung_prefix),
                    RegexMatch(r"[1-9]\d{0,2}").space(SpacePolicy.NOSPACE) @ "times",
                    UnionMatch("d", "D").space(SpacePolicy.NOSPACE),
                    RegexMatch(r"[1-9]\d{0,7}") @ "faces",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionControl.enable(FunctionControl.Responder),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_dnd_dice_handler(
    app: Ariadne, event: MessageEvent, times: RegexResult, faces: RegexResult
):
    times = int(times.result.display)
    faces = int(faces.result.display)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            "您掷出的点数是:" + " ".join([str(random.randint(1, faces)) for _ in range(times)])
        ),
    )
