import datetime
import re

import jieba
from graia.ariadne.event.message import (
    GroupMessage,
    MessageEvent,
    FriendMessage,
    TempMessage,
    ActiveGroupMessage,
    ActiveFriendMessage,
    ActiveMessage,
)
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Group, Friend
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library.orm import orm
from .pepper import pepper
from .table import ChatRecord, SendRecord
from .util import generate_pass

assert pepper

saya = Saya.current()
channel = Channel.current()

channel.name("ChatRecorder")
channel.author("nullqwertyuiop")
channel.description("一个记录聊天记录的插件，可配合词云等插件使用")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage, TempMessage], priority=0
    )
)
async def chat_record(event: MessageEvent):
    if isinstance(event, GroupMessage):
        group = event.sender.group.id
    elif isinstance(event, TempMessage):
        group = -1
    else:
        group = 0
    message = event.message_chain
    content = "".join([plain.text for plain in message.get(Plain)]).strip()
    filter_words = re.findall(r"\[mirai:(.*?)]", content, re.S)
    for i in filter_words:
        content = content.replace(f"[mirai:{i}]", "")
    if content:
        seg_result = jieba.lcut(content) if content else ""
        await orm.add(
            ChatRecord,
            {
                "time": datetime.datetime.now(),
                "field": generate_pass(group),
                "sender": generate_pass(event.sender.id),
                "persistent_string": message.as_persistent_string()[:4000],
                "seg": "|".join(seg_result)[:4000] if seg_result else "",
            },
        )


@channel.use(ListenerSchema(listening_events=[ActiveGroupMessage, ActiveFriendMessage]))
async def sent_recorder(event: ActiveMessage):
    supplicant_type = (
        "group"
        if isinstance(event.subject, Group)
        else "friend"
        if isinstance(event.subject, Friend)
        else "unknown"
    )
    msg = event.message_chain.as_persistent_string(binary=False)[:4000]
    await orm.add(
        SendRecord,
        {
            "time": datetime.datetime.now(),
            "target": event.subject.id,
            "type": supplicant_type,
            "persistent_string": msg,
        },
    )
