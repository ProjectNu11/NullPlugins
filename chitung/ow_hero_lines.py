import json
import random
from pathlib import Path

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    UnionMatch,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.depend import Blacklist, Switch, FunctionCall
from module.chitung import ASSETS, chitung_prefix
from module.chitung.utils.depends import FunctionControl

channel = Channel.current()

with Path(ASSETS, "clusters", "herolines.json").open("r", encoding="utf-8") as f:
    clusters = json.loads(f.read())


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(chitung_prefix),
                    UnionMatch("大招", "英雄不朽"),
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
        event.sender.group,
        MessageChain(
            random.choice(
                list(random.choice(clusters["ultimateAbilityHeroLines"]).values())[0]
            )
        ),
    )
