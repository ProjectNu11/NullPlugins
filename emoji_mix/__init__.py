import asyncio

from aiohttp import ClientSession
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    UnionMatch,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import config, prefix_match
from library.depend import Switch, FunctionCall, Blacklist
from library.image.oneui_mock.elements import (
    is_dark,
    Column,
    Banner,
    GeneralBox,
    HintBox,
    OneUIMock,
)
from .util import ALL_EMOJI, get_mix_emoji_url

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    UnionMatch(*ALL_EMOJI) @ "emoji1",
                    FullMatch("+", optional=True),
                    UnionMatch(*ALL_EMOJI) @ "emoji2",
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
async def emoji_mix(
    app: Ariadne, event: MessageEvent, emoji1: RegexResult, emoji2: RegexResult
):
    emoji1: str = emoji1.result.display
    emoji2: str = emoji2.result.display
    try:
        async with ClientSession() as session:
            assert (link := get_mix_emoji_url(emoji1, emoji2)), "无法获取合成链接"
            async with session.get(link, proxy=config.proxy) as resp:
                assert resp.status == 200, "图片获取失败"
                image = await resp.read()
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=image)),
        )
    except AssertionError as err:
        err_text = err.args[0]
    except Exception as err:
        err_text = str(err)
    loop = asyncio.get_event_loop()
    err_img = await loop.run_in_executor(None, compose_error, err_text)
    return await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(Image(data_bytes=err_img)),
    )


def compose_error(err_text: str) -> bytes:
    dark = is_dark()
    column = Column(dark=dark)
    banner = Banner("Emoji 合成", dark=dark)
    box = GeneralBox(text="运行搜索时出现错误", description=err_text, dark=dark)
    hint = HintBox(
        "可以尝试以下解决方案",
        "检查网络连接是否正常",
        "检查 Emoji 组合是否存在",
        dark=dark,
    )
    column.add(banner, box, hint)
    mock = OneUIMock(column, dark=dark)
    return mock.render_bytes()
