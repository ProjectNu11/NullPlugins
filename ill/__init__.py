import json
import random
from pathlib import Path

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    ParamMatch,
    ElementResult,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import PrefixMatch
from library.depend import Switch, FunctionCall

channel = Channel.current()

assets_path = Path(Path(__file__).parent, "assets")
with Path(assets_path, "ill_templates.json").open("r", encoding="UTF-8") as f:
    TEMPLATES = json.loads(f.read())["data"]


@channel.use(
    ListenerSchema(
        [GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
                    FullMatch("发病"),
                    ElementMatch(At, optional=True) @ "at",
                    ParamMatch(optional=True) @ "text",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def ill(app: Ariadne, event: MessageEvent, at: ElementResult, text: RegexResult):
    if at.matched:
        _target = at.result.target
        if _target_member := await app.get_member(event.sender.group, _target):
            target = _target_member.name
        else:
            target = _target
    elif text.matched:
        target = text.result.display
    else:
        target = event.sender.name
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(random.choice(TEMPLATES).format(target=target)),
    )
