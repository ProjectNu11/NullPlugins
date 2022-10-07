from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import prefix_match
from library.depend import Switch, FunctionCall, Blacklist
from .main import get_text

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    FullMatch("摸鱼"),
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
async def get_mofish(app: Ariadne, event: GroupMessage):
    await app.send_group_message(event.sender.group, MessageChain(get_text()))
