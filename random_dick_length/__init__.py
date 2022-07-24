import random
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexMatch,
    UnionMatch,

)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import config
from library.depend import Switch, FunctionCall


channel = Channel.current()


@channel.use(
    ListenerSchema(
        [GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch("牛子", "牛至", optional=True),
                    UnionMatch("多长", "多長", "長度", "长度", optional=True),
                ]
            )
        ],
        decorators=[Switch.check(channel.module),
                    FunctionCall.record(channel.module)],
    )
)
async def random_dick_length(app: Ariadne, event: MessageEvent):
    dick_legth = random.randint(-5, 28)
    if dick_legth > 20:
        dick_length_evaluate = "哪来的兽人，怎么会这么长"
    elif dick_legth > 15 and dick_legth <= 20:
        dick_length_evaluate = "还是蛮长的"
    elif dick_legth >= 10 and dick_legth <= 15:
        dick_length_evaluate = "到了平均水准捏"
    elif dick_legth > 0 and dick_legth < 10:
        dick_length_evaluate = "好短！"
    else:
        dick_length_evaluate = "dick ... 他 .. 他..他缩进去了！"

    await app.send_message(
        event.sender.group if isinstance(
            event, GroupMessage) else event.sender,
        MessageChain(f"你的牛子长度为{str(dick_legth)}，{str(dick_length_evaluate)}"),
    )
