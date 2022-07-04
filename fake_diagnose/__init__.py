import jieba
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source
from graia.ariadne.message.parser.twilight import RegexMatch, Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.saya.channel import Channel

from library.depend import Switch, FunctionCall

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"\w+(疼|痛)\w+")])],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def fake_diagnose(
    app: Ariadne, event: MessageEvent, source: Source, message: MessageChain
):
    msg = message.as_display()
    msg = msg.replace("疼", "癌").replace("痛", "癌")
    cut = list(jieba.cut(msg.split("癌")[0]))
    illness = f"{cut[-1]}癌"
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(f"您好！根据您的描述，您可能得了{illness}。"),
        quote=source,
    )
