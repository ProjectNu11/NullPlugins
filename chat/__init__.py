import re

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.message.parser.twilight import (
    Twilight,
    ArgumentMatch,
    WildcardMatch,
    ArgResult,
    RegexResult,
    ElementMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch, FunctionCall
from .engines import __all__
from .engines.base import BaseChat

saya = Saya.current()
channel = Channel.current()

channel.name("Chat")
channel.author("nullqwertyuiop")
channel.description("")

if not config.get_module_config(channel.module):
    config.update_module_config(
        channel.module,
        {
            "default_engine": "aiml",
            "tencent_secret_id": None,
            "tencent_secret_key": None,
        },
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At),
                    ArgumentMatch("-e", "--engine", type=str, optional=True) @ "engine",
                    ArgumentMatch(
                        "-n", "--no-translation", action="store_false", optional=True
                    )
                    @ "translate",
                    WildcardMatch().flags(re.S) @ "text",
                ]
            )
        ],
        decorators=[
            MentionMe(),
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
        ],
        priority=999,
    )
)
async def chat(
    ariadne: Ariadne,
    event: GroupMessage,
    engine: ArgResult,
    translate: ArgResult,
    text: RegexResult,
):
    engine_name = (
        engine.result
        if engine.matched
        else config.get_module_config(channel.module).get("default_engine")
    )
    engine: BaseChat
    if not (engine := __all__.get(engine_name, None)):
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"无效的聊天引擎 {engine_name}，支持的引擎有：{', '.join(__all__.keys())}"),
        )
    text: str = text.result.display
    translate: bool = translate.result if translate.matched else True
    if not text:
        return
    response = await engine.chat(text, event.sender.id, translate=translate)
    if not response:
        response = "[空内容]"
    await ariadne.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(response),
    )
