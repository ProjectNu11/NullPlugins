import asyncio
import math
import random
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image as PillowImage
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.element import Plain, At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
)
from graia.ariadne.model import MemberPerm
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

from library import config
from library.depend import Blacklist, Switch, FunctionCall
from module.chitung.utils.depends import FunctionControl
from module.chitung.vars import ASSETS, CHITUNG_PREFIX, OK_CHITUNG_PREFIX

channel = Channel.current()
winner_dir = ASSETS
c4_activation_flags = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    OK_CHITUNG_PREFIX,
                    FullMatch("winner"),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionControl.enable(FunctionControl.Lottery),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_winner_handler(app: Ariadne, event: MessageEvent):
    if member_list := await app.get_member_list(event.sender.group):
        now = datetime.now()
        guy_of_the_day = member_list[
            int(
                (now.year + now.month * 10000 + now.day * 1000000)
                * 100000000000
                / event.sender.group.id
                % len(member_list)
            )
        ]
        await app.send_group_message(
            event.sender.group, MessageChain(f"Ok Winner! {guy_of_the_day.name}")
        )
        avatar = PillowImage.open(BytesIO(await guy_of_the_day.get_avatar())).resize(
            (512, 512)
        )
        base = PillowImage.open(Path(winner_dir / "winner" / "wanted.jpg"))
        base.paste(avatar, (94, 251))
        output = BytesIO()
        base.save(output, "jpeg")
        await app.send_group_message(
            event.sender.group,
            MessageChain(
                [
                    Image(data_bytes=output.getvalue()),
                ]
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    OK_CHITUNG_PREFIX,
                    FullMatch("bummer"),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionControl.enable(FunctionControl.Lottery),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_bummer_handler(app: Ariadne, event: GroupMessage):
    group = event.sender.group
    member = event.sender
    if group.account_perm == MemberPerm.Member:
        await app.send_group_message(
            group, MessageChain(f"{config.name}目前还没有管理员权限，请授予{config.name}权限解锁更多功能。")
        )
        return
    if member_list := await app.get_member_list(group):
        if normal_members := [
            m for m in member_list if m.permission == MemberPerm.Member
        ]:
            victim = random.choice(normal_members)
            await app.mute_member(group, victim, 120)
            if member.permission == MemberPerm.Member:
                if member.id != victim.id:
                    await app.mute_member(group, member, 120)
                    await app.send_group_message(
                        group,
                        MessageChain(
                            [
                                Plain(f"Ok Bummer! {victim.name}\n"),
                                At(member),
                                Plain(" 以自己为代价随机带走了 "),
                                At(victim),
                            ]
                        ),
                    )
                    return
                await app.send_group_message(
                    group,
                    MessageChain(
                        [
                            Plain(
                                text=f"Ok Bummer! {victim.name}\n"
                                f"{member.name} 尝试随机极限一换一。他成功把自己换出去了！"
                            )
                        ]
                    ),
                )
                return
            await app.send_group_message(
                group,
                MessageChain(
                    [
                        Plain(f"Ok Bummer! {victim.name}\n管理员"),
                        At(member),
                        Plain(" 随机带走了 "),
                        At(victim),
                    ]
                ),
            )
        else:
            await app.send_group_message(
                group, MessageChain("全都是管理员的群你让我抽一个普通成员禁言？别闹。")
            )

        return


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    OK_CHITUNG_PREFIX,
                    FullMatch("c4"),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionControl.enable(FunctionControl.Lottery),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_c4_handler(app: Ariadne, event: MessageEvent):
    group = event.sender.group
    member = event.sender
    if group.account_perm == MemberPerm.Member:
        await app.send_group_message(
            group,
            MessageChain(f"{CHITUNG_PREFIX}目前还没有管理员权限，请授予{CHITUNG_PREFIX}权限解锁更多功能。"),
        )
        return
    if group.id in c4_activation_flags:
        await app.send_group_message(group, MessageChain("今日的C4已经被触发过啦！请明天再来尝试作死！"))
        return
    if member_list := await app.get_member_list(group):
        if random.random() < 1 / math.sqrt(len(member_list)):
            await app.mute_all(group)
            c4_activation_flags.append(group.id)
            await app.send_group_message(group, MessageChain("中咧！"))
            await app.send_group_message(
                group,
                MessageChain([At(member), Plain(text=" 成功触发了C4！大家一起恭喜TA！")]),
            )
            await asyncio.sleep(300)
            await app.unmute_all(group)
        else:
            await app.send_group_message(group, MessageChain("没有中！"))


@channel.use(SchedulerSchema(timer=timers.crontabify("0 6 * * *")))
async def chitung_c4_flush():
    global c4_activation_flags
    c4_activation_flags = []
