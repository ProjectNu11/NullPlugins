import re

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    ArgumentMatch,
    WildcardMatch,
    ArgResult,
    RegexResult,
    UnionMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import PrefixMatch
from library.config import config
from library.depend import Switch, FunctionCall, Blacklist
from .engines import __all__

saya = Saya.current()
channel = Channel.current()

channel.name("Translator")
channel.author("nullqwertyuiop")
channel.description("")

if not config.get_module_config(channel.module):
    config.update_module_config(
        channel.module,
        {
            "default_engine": "youdao",
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
                    PrefixMatch,
                    UnionMatch("translate", "翻译"),
                    ArgumentMatch("-e", "--engine", type=str, optional=True) @ "engine",
                    ArgumentMatch("-s", "--source", type=str, optional=True) @ "source",
                    ArgumentMatch("-t", "--target", type=str, optional=True) @ "target",
                    ArgumentMatch("-k", "--keep", type=str, optional=True) @ "keep",
                    WildcardMatch().flags(re.S) @ "text",
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
async def translate(
    ariadne: Ariadne,
    event: GroupMessage,
    engine: ArgResult,
    source: ArgResult,
    target: ArgResult,
    keep: ArgResult,
    text: RegexResult,
):
    engine_name = (
        engine.result
        if engine.matched
        else config.get_module_config(channel.module).get("default_engine")
    )
    if not (data := __all__.get(engine_name, None)):
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"无效的翻译引擎 {engine_name}，支持的引擎有：{', '.join(__all__.keys())}"),
        )
    engine, languages = data
    trans_from: str = source.result if source.matched else None
    trans_to: str = target.result if target.matched else None
    if (trans_from is not None and trans_from not in languages) or (
        trans_to is not None and trans_to not in languages
    ):
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"不支持的语言，支持的语言有：{', '.join(languages)}"),
        )
    keep: str = keep.result if keep.matched else None
    text: str = text.result.display
    if not text:
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain("请输入要翻译的文本"),
        )
    if engine_name == "tencent":
        translated = await engine.trans(
            content=text, trans_from=trans_from, trans_to=trans_to, keep=keep
        )
    else:
        translated = await engine.trans(
            content=text, trans_from=trans_from, trans_to=trans_to
        )
    if not translated:
        translated = "[空内容]"
    await ariadne.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(translated),
    )
