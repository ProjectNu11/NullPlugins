import json
import random
from pathlib import Path

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.depend import Blacklist, Switch, FunctionCall
from module.chitung.utils.depends import FunctionControl
from module.chitung.vars import ASSETS

with Path(ASSETS, "clusters", "autoreply.json").open("r", encoding="utf-8") as f:
    CLUSTERS = json.loads(f.read())

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r"[Hh](i|ello)"),
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
async def chitung_greeting(app: Ariadne, event: GroupMessage):
    await app.send_group_message(
        event.sender.group, MessageChain(random.choice(["Hi", "Hello", "Hey"]))
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r".*(下线了|我走了|拜拜).*"),
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
async def chitung_goodbye(app: Ariadne, event: GroupMessage):
    await app.send_group_message(
        event.sender.group,
        MessageChain(random.choice(list(CLUSTERS["goodbyeReplyLines"].values()))),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r".*(([Oo])verwatch|守望((先锋)|(屁股))|([玩打])((OW)|(ow))).*"),
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
async def chitung_anti_ow(app: Ariadne, event: GroupMessage):
    await app.send_group_message(
        event.sender.group,
        MessageChain(
            random.choice(list(CLUSTERS["antiOverwatchGameReplyLines"].values()))
        ),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(
                        r".*(([日干操艹草滚])([你尼泥])([妈马麻])|"
                        r"([Mm])otherfucker|([Ff])uck).*"
                    ),
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
async def chitung_anti_dirty_words(app: Ariadne, event: GroupMessage):
    await app.send_group_message(
        event.sender.group,
        MessageChain(
            random.choice(list(CLUSTERS["antiDirtyWordsReplyLines"].values()))
        ),
    )
