import asyncio
import contextlib
import itertools
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image as PillowImage
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.exception import UnknownTarget, RemoteException, AccountMuted
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
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

from library import config, prefix_match
from library.depend import Permission, FunctionCall, Switch, Blacklist
from library.image.oneui_mock.elements import GeneralBox, Column, Banner, OneUIMock
from library.model import UserPerm
from library.orm import orm
from library.orm.table import FunctionCallRecord
from module import modules
from module.chat_recorder import SendRecord, ChatRecord, generate_pass

channel = Channel.current()

channel.name("MsgStat")
channel.author("nullqwertyuiop")
channel.description("收发信统计")

ICON = PillowImage.open(Path(__file__).parent / "icon.png")


async def generate_msg_stat(func: str | int) -> tuple[GeneralBox, GeneralBox]:
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
        return (
            GeneralBox(f"{func}统计"),
            GeneralBox()
            .add(text="72 小时", description=f"{stat_72} 条", highlight=True)
            .add(text="36 小时", description=f"{stat_36} 条", highlight=True)
            .add(text="24 小时", description=f"{stat_24} 条", highlight=True)
            .add(text="12 小时", description=f"{stat_12} 条", highlight=True)
            .add(text="6 小时", description=f"{stat_6} 条", highlight=True)
            .add(text="3 小时", description=f"{stat_3} 条", highlight=True)
            .add(text="1 小时", description=f"{stat_1} 条", highlight=True),
        )
    return GeneralBox(f"{func}统计"), GeneralBox().add("暂无数据")


async def generate_call_stat(sender: int = None) -> tuple[GeneralBox, GeneralBox]:
    if sender:
        query = select(FunctionCallRecord.function).where(
            FunctionCallRecord.time > datetime.now() - timedelta(days=30),
            FunctionCallRecord.supplicant == sender,
        )
    else:
        query = select(FunctionCallRecord.function).where(
            FunctionCallRecord.time > datetime.now() - timedelta(days=1)
        )
    header = GeneralBox("模块调用统计")
    if data := await orm.all(query):
        stat = {}
        for func in data:
            stat[func[0]] = stat.get(func[0], 0) + 1
        box = GeneralBox()
        for func, value in sorted(stat.items(), key=lambda x: x[1], reverse=True):
            box.add(
                module.name if (module := modules.get(func)) else func,
                description=f"{value} 次",
                highlight=True,
            )
        return header, box
    return header, GeneralBox().add("暂无数据")


async def generate_all(supplicant: int = None) -> OneUIMock:
    if supplicant:
        boxes = [
            *(await generate_msg_stat(supplicant)),
            *(await generate_call_stat(supplicant)),
        ]
    else:
        boxes = [
            *(await generate_msg_stat("收信")),
            *(await generate_msg_stat("发信")),
            *(await generate_call_stat()),
        ]
    return OneUIMock(
        Column(Banner("统计", icon=ICON), *(boxes[-2:])), Column(*boxes[:-2])
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
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
            box = await generate_msg_stat(func)
        else:
            box = await generate_call_stat()
        mock = OneUIMock(Column(Banner("统计", icon=ICON), *box))
    else:
        mock = await generate_all()
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(Image(data_bytes=await mock.async_render_bytes())),
    )


@channel.use(SchedulerSchema(timer=timers.crontabify("0 0 * * *")))
async def send_daily(app: Ariadne):
    image_bytes = await (await generate_all()).async_render_bytes()
    with contextlib.suppress(UnknownTarget, RemoteException, AccountMuted):
        for owner in config.owners:
            await app.send_friend_message(
                owner, MessageChain(Image(data_bytes=image_bytes))
            )
            await asyncio.sleep(1)
        for dev_group in config.dev_group:
            await app.send_group_message(
                dev_group, MessageChain(Image(data_bytes=image_bytes))
            )
            await asyncio.sleep(1)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
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
            box = await generate_msg_stat(event.sender.id)
        else:
            box = await generate_call_stat(event.sender.id)
        mock = OneUIMock(Column(Banner("统计", icon=ICON), *box))
    else:
        mock = await generate_all(event.sender.id)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(Image(data_bytes=await mock.async_render_bytes())),
    )
