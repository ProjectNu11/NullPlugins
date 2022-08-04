import asyncio
import contextlib
import re
from io import BytesIO

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    ArgumentMatch,
    WildcardMatch,
    ArgResult,
    RegexResult,
    FullMatch,
    SpacePolicy,
)
from graia.ariadne.model import Group, Friend
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch, FunctionCall
from .engines import __all__, BaseSearch, run_search

saya = Saya.current()
channel = Channel.current()

channel.name("Chat")
channel.author("nullqwertyuiop")
channel.description("")

if not (__cfg := config.get_module_config(channel.module)):
    config.update_module_config(
        channel.module,
        {
            "default_engine": "netease",
        },
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                    FullMatch("点歌"),
                    ArgumentMatch("-e", "--engine", type=str, optional=True) @ "engine",
                    WildcardMatch().flags(re.S) @ "keywords",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
        ],
    )
)
async def furry_pic_search(
    ariadne: Ariadne,
    event: GroupMessage,
    engine: ArgResult,
    keywords: RegexResult,
):
    engine_name = (
        engine.result
        if engine.matched
        else config.get_module_config(channel.module).get("default_engine")
    )
    engine: BaseSearch
    if not (engine := __all__.get(engine_name, None)):
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"无效的搜索引擎 {engine_name}，支持的引擎有：{', '.join(__all__.keys())}"),
        )
    keywords = keywords.result.display.split() if keywords.matched else []

    image, music = await run_search(engine, *keywords)
    image = image.convert("RGB")
    output = BytesIO()
    image.save(output, format="jpeg")

    if not music:
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=output.getvalue())),
        )

    await ariadne.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(Image(data_bytes=output.getvalue())),
    )

    _max_count = len(music)

    try:
        if isinstance(event, GroupMessage):

            async def waiter(
                _group: Group,
                _event: GroupMessage,
            ):
                if (
                    _event.sender.id == event.sender.id
                    and _group.id == event.sender.group.id
                ):
                    if _plain := _event.message_chain.get(Plain):
                        _msg = MessageChain(_plain).display
                        if _msg.isdigit():
                            _msg = int(_msg)
                            return _msg if 0 < _msg <= _max_count else _max_count

            count = await FunctionWaiter(waiter, [GroupMessage]).wait(60)
        else:

            async def waiter(
                _friend: Friend,
                _event: FriendMessage,
            ):
                if _event.sender.id == event.sender.id:
                    if _plain := _event.message_chain.get(Plain):
                        _msg = MessageChain(_plain).display
                        if _msg.isdigit():
                            _msg = int(_msg)
                            return _msg if 0 < _msg <= _max_count else _max_count

            count = await FunctionWaiter(waiter, [FriendMessage]).wait(60)
    except asyncio.exceptions.TimeoutError:
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain("超时，已取消本次查询"),
        )

    await ariadne.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(music[count - 1]),
    )
