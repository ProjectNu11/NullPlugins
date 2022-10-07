import asyncio
import re
from io import BytesIO

from PIL import Image as PillowImage
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Quote
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    WildcardMatch,
    RegexResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import prefix_match, config
from library.depend import Switch, FunctionCall, Interval, Blacklist
from library.help import module_help
from library.image.oneui_mock.elements import GeneralBox
from .function import __all__, check_and_run
from .util import get_element_image, get_image

saya = Saya.current()
channel = Channel.current()

channel.name("AvatarFunPic")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    UnionMatch(*__all__.keys()) @ "func",
                    WildcardMatch().flags(re.S) @ "content",
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
async def avatar_fun(
    app: Ariadne, event: MessageEvent, func: RegexResult, content: RegexResult
):
    await Interval.check_and_raise(
        channel.module,
        supplicant=event.sender,
        seconds=15,
        on_failure=MessageChain("休息一下罢！冷却 {interval}"),
    )
    elements = [PillowImage.open(BytesIO(await get_image(event.sender.id)))]
    if _quote := event.message_chain.get(Quote):
        quote: Quote = _quote[0]
        _msg: MessageEvent = await app.get_message_from_id(
            quote.id, target=quote.target_id
        )
        _content = _msg.message_chain
    else:
        _content = content.result
    elements.extend(await get_element_image(_content))
    loop = asyncio.get_event_loop()
    try:
        if not (
            composed := await loop.run_in_executor(
                None, check_and_run, func.result.display, *elements
            )
        ):
            return
        msg = MessageChain([Image(data_bytes=composed)])
    except AssertionError as err:
        msg = MessageChain(err.args[0])
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        msg,
    )


module_help(channel.module).add(
    GeneralBox(divider=False)
    .add("使用方法", "发送 指令前缀以及对应功能名 即可")
    .add("指令前缀", " ".join([f'"{prefix}"' for prefix in config.func.prefix]))
    .add("功能列表", "\n".join(__all__.keys()))
)
