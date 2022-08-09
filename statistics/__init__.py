import asyncio
import contextlib
import itertools
from datetime import datetime, timedelta

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Forward, ForwardNode
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    UnionMatch,
    MatchResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema
from sqlalchemy import select

from library import config, PrefixMatch
from library.depend import Permission, FunctionCall, Switch, Blacklist
from library.model import UserPerm
from library.orm import orm
from library.orm.table import FunctionCallRecord
from module import modules
from module.chat_recorder import SendRecord, ChatRecord, generate_pass

channel = Channel.current()

channel.name("MsgStat")
channel.author("nullqwertyuiop")
channel.description("收发信统计")


async def generate_msg_stat(func: str | int):
    if func == "收信":
        query = select(ChatRecord.time, ChatRecord.id).where(
            ChatRecord.time > datetime.now() - timedelta(days=3)
        )
    elif func == "发信":
        query = select(SendRecord.time, SendRecord.id).where(
            SendRecord.time > datetime.now() - timedelta(days=3)
        )
    else:
        query = select(ChatRecord.time, ChatRecord.id).where(
            ChatRecord.time > datetime.now() - timedelta(days=3),
            ChatRecord.sender == generate_pass(func),
        )
        func = "消息"
    if data := await orm.all(query):
        stat = {
            key: len(list(items))
            for key, items in itertools.groupby(
                data, lambda x: int((datetime.now() - x[0]).total_seconds() // 3600)
            )
        }
        stat_72 = sum(x for key, x in stat.items() if key <= 72)
        stat_36 = sum(x for key, x in stat.items() if key <= 36)
        stat_24 = sum(x for key, x in stat.items() if key <= 24)
        stat_12 = sum(x for key, x in stat.items() if key <= 12)
        stat_6 = sum(x for key, x in stat.items() if key <= 6)
        stat_3 = sum(x for key, x in stat.items() if key <= 3)
        stat_1 = sum(x for key, x in stat.items() if key <= 1)
        return MessageChain(
            [
                Plain(f"[{func}统计]\n"),
                Plain(f"72 小时 | {stat_72} 条\n"),
                Plain(f"36 小时 | {stat_36} 条\n"),
                Plain(f"24 小时 | {stat_24} 条\n"),
                Plain(f"12 小时 | {stat_12} 条\n"),
                Plain(f" 6 小时 | {stat_6} 条\n"),
                Plain(f" 3 小时 | {stat_3} 条\n"),
                Plain(f" 1 小时 | {stat_1} 条"),
            ]
        )
    return MessageChain(f"[{func}统计]\n暂无数据")


async def generate_call_stat(sender: int = None):
    stat = {}
    if sender:
        query = select(FunctionCallRecord.function).where(
            FunctionCallRecord.time > datetime.now() - timedelta(days=30),
            FunctionCallRecord.supplicant == sender,
        )
    else:
        query = select(FunctionCallRecord.function).where(
            FunctionCallRecord.time > datetime.now() - timedelta(days=1)
        )
    if data := await orm.all(query):
        for func in data:
            stat[func[0]] = stat.get(func[0], 0) + 1
        messages = ["[模块调用统计]"]
        for func, value in sorted(stat.items(), key=lambda x: x[1], reverse=True):
            messages.append(
                f"{module.name} | {value} 次"
                if (module := modules.get(func))
                else f"{func} | {stat[func]} 次"
            )
        return MessageChain(["\n".join(messages)])
    return MessageChain(f"[模块调用统计]\n暂无数据")


async def generate_all(supplicant: int = None):
    if supplicant:
        messages = [
            await generate_msg_stat(supplicant),
            await generate_call_stat(supplicant),
        ]
    else:
        messages = [
            await generate_msg_stat("收信"),
            await generate_msg_stat("发信"),
            await generate_call_stat(),
        ]
    return MessageChain(
        [
            Forward(
                ForwardNode(
                    target=config.account,
                    name=f"{config.name}#{config.num}",
                    time=datetime.now(),
                    message=message,
                )
                for message in messages
            )
        ]
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
                    UnionMatch("收信", "发信", "模块", "调用", "模块调用", optional=True) @ "which",
                    FullMatch("统计"),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Permission.require(
                UserPerm.BOT_OWNER, MessageChain("权限不足，你需要来自 所有人 的权限才能进行本操作")
            ),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def stats_handler(app: Ariadne, event: MessageEvent, which: MatchResult):
    if which.matched:
        func = which.result.display
        if func in ("收信", "发信"):
            msg = await generate_msg_stat(func)
        else:
            msg = await generate_call_stat()
    else:
        msg = await generate_all()
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        msg,
    )


@channel.use(SchedulerSchema(timer=timers.crontabify("0 0 * * *")))
async def send_daily(app: Ariadne):
    message = await generate_all()
    with contextlib.suppress(UnknownTarget):
        for owner in config.owners:
            await app.send_friend_message(owner, message)
            await asyncio.sleep(1)
        for dev_group in config.dev_group:
            await app.send_group_message(dev_group, message)
            await asyncio.sleep(1)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
                    FullMatch("我的"),
                    UnionMatch("消息", "模块", "调用", "模块调用", optional=True) @ "which",
                    FullMatch("统计"),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
        ],
    )
)
async def stats_no_permission_handler(
    app: Ariadne, event: MessageEvent, which: MatchResult
):
    if which.matched:
        func = which.result.display
        if func == "消息":
            msg = await generate_msg_stat(event.sender.id)
        else:
            msg = await generate_call_stat(event.sender.id)
    else:
        msg = await generate_all(event.sender.id)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        msg,
    )
