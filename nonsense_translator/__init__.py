import random
import re

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    SpacePolicy,
    ArgumentMatch,
    WildcardMatch,
    ArgResult,
    RegexResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch, FunctionCall
from module.translator.engines import BaseTrans, get_engine, get_languages

saya = Saya.current()
channel = Channel.current()

channel.name("NonsenseTranslate")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                    FullMatch("瞎翻译"),
                    ArgumentMatch("-e", "--engine", type=str, optional=True) @ "engine",
                    ArgumentMatch("-t", "--times", type=int, optional=True) @ "times",
                    WildcardMatch().flags(re.S) @ "text",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def nonsense_translate(
    ariadne: Ariadne,
    event: GroupMessage,
    engine: ArgResult,
    times: ArgResult,
    text: RegexResult,
):
    trans_engine: BaseTrans = get_engine(engine.result if engine.matched else None)
    languages: list[str] = get_languages(engine.result if engine.matched else None)
    if trans_engine is None or languages is None:
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain("无效的引擎"),
        )
    times: int = times.result if times.matched else 20
    text = text.result.display
    if times <= 0 or not text:
        return await ariadne.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain("？这是在干什么"),
        )
    for _ in range(times - 1):
        text = await trans_engine.trans(text, trans_to=random.choice(languages))
    text = await trans_engine.trans(text)
    await ariadne.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(text),
    )
