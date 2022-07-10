from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, SpacePolicy
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import config
from library.depend import Switch, FunctionCall
from .main import get_text

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                    FullMatch("摸鱼"),
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def get_mofish(app: Ariadne, event: GroupMessage):
    await app.send_group_message(event.sender.group, MessageChain(get_text()))
