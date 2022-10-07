import re
from io import BytesIO

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    ArgumentMatch,
    WildcardMatch,
    ArgResult,
    RegexResult,
    FullMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import prefix_match
from library.config import config
from library.depend import Switch, FunctionCall, Blacklist
from .engines import __all__, BaseSearch, run_search, __cfg__

saya = Saya.current()
channel = Channel.current()

channel.name("Chat")
channel.author("nullqwertyuiop")
channel.description("")

if not (__cfg := config.get_module_config(channel.module)):
    config.update_module_config(
        channel.module,
        {
            "default_engine": "e621",
            **{engine: {key: None for key in keys} for engine, keys in __cfg__.items()},
        },
    )
else:
    for __engine, __keys in __cfg__.items():
        if __cfg.get(__engine, None) is None:
            __cfg.update({__engine: {key: None for key in __keys}})
            continue
        for __key in __keys:
            if __cfg.get(__engine, {}).get(__key, None) is None:
                __cfg[__engine].update({__key: None})
    config.update_module_config(channel.module, __cfg)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    FullMatch("兽图"),
                    ArgumentMatch("-n", "--no-random", optional=True) @ "no_random",
                    ArgumentMatch("-e", "--engine", type=str, optional=True) @ "engine",
                    WildcardMatch().flags(re.S) @ "tags",
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
async def furry_pic_search(
    ariadne: Ariadne,
    event: GroupMessage,
    engine: ArgResult,
    no_random: ArgResult,
    tags: RegexResult,
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
    tags = tags.result.display.split() if tags.matched else []
    get_random = not no_random.matched
    await ariadne.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            Image(data_bytes=await run_search(engine, *tags, get_random=get_random))
        ),
    )
