import random

from graia.ariadne import Ariadne
from graia.ariadne.event.message import (
    GroupMessage,
    MessageEvent,
    FriendMessage,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
    FullMatch,
    RegexResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library.depend import Switch, FunctionCall

saya = Saya.current()
channel = Channel.current()

channel.name("dice")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r"\d+") @ "times",
                    FullMatch("d"),
                    RegexMatch(r"\d+") @ "faces",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chat_record(
    app: Ariadne, event: MessageEvent, times: RegexResult, faces: RegexResult
):
    times = int(times.result.display)
    if times > 1000:
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain("投掷次数过多"),
        )

    faces = int(faces.result.display)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            [
                Plain(
                    " ".join(
                        [f"{random.randint(1, faces)}/{faces}" for _ in range(times)]
                    )
                )
            ]
        ),
    )
