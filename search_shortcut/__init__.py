import re
import urllib.parse

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    SpacePolicy,
    WildcardMatch,
    MatchResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library.depend import Switch, FunctionCall
from library.depend.blacklist import Blacklist

saya = Saya.current()
channel = Channel.current()

channel.name("SearchShortcut")
channel.author("nullqwertyuiop")
channel.description("自己查")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("百度").space(SpacePolicy.FORCE).flags(re.S),
                    WildcardMatch() @ "content",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
            Blacklist.check(),
        ],
    )
)
async def search_shortcut(app: Ariadne, event: MessageEvent, content: MatchResult):
    if content := content.result.display:
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"https://www.baidu.com/s?wd={urllib.parse.quote(content)}"),
            quote=event.message_chain.get_first(Source),
        )
