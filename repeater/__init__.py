from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, ActiveGroupMessage
from graia.ariadne.message.element import (
    Image,
    Plain,
    At,
    Quote,
    AtAll,
    Face,
    Poke,
    Forward,
    App,
    Json,
    Xml,
    MarketFace,
    MultimediaElement,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library.depend import Switch, FunctionCall

saya = Saya.current()
channel = Channel.current()

channel.name("Repeater")
channel.author("nullqwertyuiop")
channel.description("人类的本质")

group_repeat = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[Switch.check(channel.module)]
    )
)
async def repeater(app: Ariadne, event: GroupMessage):
    global group_repeat
    message = event.messageChain
    group = event.sender.group
    if (
        message.has(Forward)
        or message.has(App)
        or message.has(Json)
        or message.has(Xml)
        or message.has(MarketFace)
    ):
        group_repeat[group.id] = {"msg": message.asPersistentString(), "count": -1}
        return
    msg = message.copy()
    for i in msg.__root__:
        if isinstance(i, MultimediaElement):
            i.url = ""
    message_serialization = msg.asPersistentString()
    if group.id not in group_repeat.keys():
        group_repeat[group.id] = {"msg": message_serialization, "count": 1}
    elif message_serialization == group_repeat[group.id]["msg"]:
        if group_repeat[group.id]["count"] == -1:
            return
        count = group_repeat[group.id]["count"] + 1
        if count == 3:
            group_repeat[group.id]["count"] = count
            msg = message.include(Plain, Image, At, Quote, AtAll, Face, Poke)
            if msg.asDisplay() == "<! 不支持的消息类型 !>":
                group_repeat[group.id] = {
                    "msg": msg.asPersistentString(),
                    "count": -1,
                }
                return
            await app.sendGroupMessage(group, msg.asSendable())
            await FunctionCall.add_record(channel.module, event)
        else:
            group_repeat[group.id]["count"] = count
        return
    else:
        group_repeat[group.id]["msg"] = message_serialization
        group_repeat[group.id]["count"] = 1


@channel.use(ListenerSchema(listening_events=[ActiveGroupMessage]))
async def repeater_flush(event: ActiveGroupMessage):
    global group_repeat
    group_repeat[event.subject.id] = {
        "msg": event.messageChain.asPersistentString(),
        "count": -1,
    }
