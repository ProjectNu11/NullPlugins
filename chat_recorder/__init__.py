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

from library.help import Disclaimer
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


Disclaimer.register(
    "聊天记录的储存与使用",
    "在您未拒绝接受储存聊天内容的情况下，本项目会在所在服务器的数据库中保存和取用您的聊天内容，以便您能使用依赖于聊天内容的本项目功能。",
    "您有权选择保存或拒绝保存聊天内容。您可以通过在群组内或私聊发送相关指令的方式拒绝保存聊天内容。但如果您选择拒"
    "绝保存聊天内容，则您可能无法使用依赖于聊天内容的本项目功能。",
    "您有权请求下载聊天内容归档或从本项目所在服务器的数据库中删除有关您的聊天内容，详细操作请咨询管理员。",
    "通过本项目所保存聊天内容所取得的有关信息将适用于本政策。",
)
