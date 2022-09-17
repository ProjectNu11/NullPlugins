import asyncio
import math
import random
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

from graia.ariadne import Ariadne
from graia.ariadne.event.message import (
    Member,
    GroupMessage,
    FriendMessage,
    MessageEvent,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
    UnionMatch,
    FullMatch,
    RegexResult,
)
from graia.ariadne.model import Friend
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

from library.depend import Switch, FunctionCall
from library.depend.interval import Interval

from library import config
from library.depend import Switch, FunctionCall


channel = Channel.current()

assets_path = Path(Path(__file__).parent, "assets")
with Path(assets_path, "fct.json").open("r", encoding="UTF-8") as f:
    TEMPLATES = json.loads(f.read())["text"]


@channel.use(
    ListenerSchema(
        [GroupMessage, FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("疯狂星期四")])],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def random_dick_length(app: Ariadne, event: MessageEvent):

    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(random.choice(TEMPLATES)),
    )
