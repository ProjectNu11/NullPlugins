import asyncio
import contextlib
import re

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    UnionMatch,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

from library import prefix_match
from library.depend import Switch, FunctionCall, Blacklist
from .util import (
    run_once,
    INTERVAL,
    compose,
    bulk_fetch_from_db,
    registered,
    compose_error,
    register,
    fetch_from_db,
    unregister,
    compose_general,
    QUERY_INTERVAL,
)

channel = Channel.current()


@channel.use(SchedulerSchema(timer=timers.every_custom_minutes(QUERY_INTERVAL)))
async def snowball_fetch_news():
    await run_once()


@channel.use(SchedulerSchema(timer=timers.every_custom_minutes(INTERVAL)))
async def snowball_send_news(app: Ariadne):
    with contextlib.suppress(UnknownTarget, AssertionError):
        news = await bulk_fetch_from_db(set_sent=True)
        img = await compose(*news)
        data = registered.get()
        for group in data["group"]:
            await app.send_group_message(group, MessageChain(Image(data_bytes=img)))
            await asyncio.sleep(1)
        for friend in data["friend"]:
            await app.send_friend_message(friend, MessageChain(Image(data_bytes=img)))
            await asyncio.sleep(1)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    FullMatch("实时新闻"),
                    UnionMatch("开启", "关闭", "查看", optional=True) @ "func",
                    WildcardMatch() @ "args",
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
async def snowball_news(
    app: Ariadne, event: MessageEvent, func: RegexResult, args: RegexResult
):
    try:
        assert func.matched, "未指定功能，可选的功能有：开启、关闭、查看"
        function: str = func.result.display
        if function == "查看":
            assert args.matched, "未指定参数，可选的参数有 [编号]、[数字]条"
            arguments: str = args.result.display
            is_number: bool = arguments.isdigit()
            if _match := re.findall(r"(\d+)条?", arguments):
                _match = int(_match[0])
            if is_number:
                assert (news := await fetch_from_db(_match)), "数据库中暂无该编号的新闻"
                return await app.send_message(
                    event.sender.group
                    if isinstance(event, GroupMessage)
                    else event.sender,
                    MessageChain(
                        [
                            Plain(f"标题：{news.title}\n"),
                            Plain(f"摘要：{news.text}\n"),
                            Plain(f"链接：{news.target}\n"),
                            Plain(
                                f"时间：{news.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                            ),
                        ]
                    ),
                )
            assert _match <= 50, "最多只能查看最新的 50 条新闻"
            news = await bulk_fetch_from_db(count=_match, set_sent=False)
            img = await compose(*news)
            return await app.send_message(
                event.sender.group if isinstance(event, GroupMessage) else event.sender,
                MessageChain(Image(data_bytes=img)),
            )
        if isinstance(event, GroupMessage):
            reg_args = {"group": event.sender.group.id}
        else:
            reg_args = {"friend": event.sender.id}
        if function == "开启":
            register(**reg_args)
            title = "已订阅实时新闻"
            description = f"将每 {INTERVAL} 分钟推送一次实时新闻"
        else:
            unregister(**reg_args)
            title = "已取消订阅实时新闻"
            description = "将不再推送实时新闻"
        img = await compose_general(title, description)
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=img)),
        )
    except AssertionError as err:
        err_text = err.args[0]
        img = await compose_error(err_text)
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=img)),
        )
