import asyncio
import random
from datetime import datetime, timedelta
from itertools import groupby

from graia.ariadne import Ariadne, get_running
from graia.ariadne.event.message import GroupMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import ForwardNode, Plain, Forward
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ArgumentMatch,
    ArgResult,
)
from graia.ariadne.model import MemberPerm, MemberInfo, Group, Member
from graia.broadcast.interrupt import Waiter, InterruptControl
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from sqlalchemy import select

from library.config import config
from library.depend import Switch, FunctionCall
from library.orm import orm
from module.namecard_shuffle.table import NameCardBackup

saya = Saya.current()
channel = Channel.current()

channel.name("NameCardShuffle")
channel.author("nullqwertyuiop, 角川烈&白门守望者 (Chitung-public)")
channel.description("")

bcc = saya.broadcast
inc = InterruptControl(bcc)

last_active = datetime.fromtimestamp(0)
shuffle_flags = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(".shuffle"),
                    ArgumentMatch("-r", "--restore", action="store_true") @ "restore",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def name_card_shuffle(app: Ariadne, event: MessageEvent, restore: ArgResult):
    global last_active, shuffle_flags
    group = event.sender.group
    if str(group.id) in shuffle_flags and shuffle_flags[str(group.id)]["status"] == 1:
        await app.sendGroupMessage(group, MessageChain("已在进行群名片打乱"))
        return
    if last_active + timedelta(minutes=2) > datetime.now():
        seconds = (last_active + timedelta(minutes=2) - datetime.now()).total_seconds()
        await app.sendGroupMessage(
            group,
            MessageChain("距离上一次 shuffle 运行时间不满 2 分钟，请在 " f"{round(seconds, 2)} 秒后再试。"),
        )
        return
    if group.accountPerm == MemberPerm.Member:
        await app.sendGroupMessage(
            group, MessageChain(f"{config.name} 目前还没有管理员权限，请授予 {config.name} 权限解锁更多功能。")
        )
        return
    if restore.matched:
        last_active = datetime.now()
        return await restore_name_card(group, event.sender)
    if not (member_list := await app.getMemberList(group)):
        return
    if len(member_list) > 20:
        await app.sendGroupMessage(
            group, MessageChain("群人数大于设定的人数限制，仅对最近发言的 20 人进行打乱。")
        )
    original_info = [(member, member.name) for member in member_list]
    original_info = sorted(
        original_info, key=lambda x: x[0].lastSpeakTimestamp, reverse=True
    )[:20]
    shuffled_name = [
        member_info[1] if member_info[1] not in ["null", "Null"] else "<! 不合法的名片 !>"
        for member_info in original_info
    ]
    random.shuffle(shuffled_name)
    shuffle_flags[str(group.id)] = {"status": 1}
    shuffle_list = [
        (original_info[x][0], shuffled_name[x]) for x in range(len(original_info))
    ]
    last_active = datetime.now()
    await update_name_card(name_list=shuffle_list, time=last_active)
    await app.sendGroupMessage(group, MessageChain("已完成本次群名片打乱\nHave fun!"))
    await asyncio.sleep(120)
    await update_name_card(name_list=original_info, backup=False)
    last_active = datetime.now()
    shuffle_flags[str(group.id)]["status"] = 0
    await app.sendGroupMessage(group, MessageChain("已恢复本次群名片打乱"))


async def update_name_card(
    name_list: list, *, time: datetime = None, backup: bool = True
):
    ariadne = get_running(Ariadne)
    for target, new_name in name_list:
        await asyncio.sleep(0.25)
        if backup and time:
            await add_backup(
                time=time,
                group=target.group.id,
                member=target.id,
                before=target.name,
                after=new_name,
            )
        await ariadne.modifyMemberInfo(target, MemberInfo(name=new_name))


async def add_backup(time: datetime, group: int, member: int, before: str, after: str):
    await orm.add(
        NameCardBackup,
        {
            "time": time,
            "group": group,
            "member": member,
            "before": before,
            "after": after,
        },
    )


async def query_backup(group: int):
    if fetch := await orm.fetchall(
        select(
            NameCardBackup.time,
            NameCardBackup.member,
            NameCardBackup.before,
            NameCardBackup.after,
        ).where(NameCardBackup.group == group)
    ):
        assert isinstance(fetch, list)
        return list(
            map(
                lambda x: list(x[1]),
                groupby(
                    sorted(fetch, key=lambda x: x[0], reverse=True), key=lambda x: x[0]
                ),
            )
        )


async def restore_name_card(group: Group, supplicant: Member):
    ariadne = get_running(Ariadne)
    if not (history := await query_backup(group.id)):
        await ariadne.sendGroupMessage(group, MessageChain("暂无本群打乱历史"))
    history = history[:20]
    count = len(history)
    fwd_nodes = [
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now(),
            message=MessageChain(f"本群共有 {count} 条打乱历史\n\n可在 1 分钟内发送序号进行恢复操作"),
        )
    ] + [
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now() + timedelta(seconds=15) * (index + 1),
            message=MessageChain.create(
                [
                    Plain(f"#{index + 1} "),
                    Plain(chunk[0][0].strftime("%Y年%m月%d日 %H:%M:%S")),
                ]
                + [
                    Plain(f"\n\n{before} -> {after}")
                    for _, _, before, after in list(chunk)
                ]
            ),
        )
        for index, chunk in enumerate(history)
    ]
    await ariadne.sendGroupMessage(
        group,
        MessageChain.create([Forward(nodeList=fwd_nodes)]),
    )

    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def response_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if waiter_group.id == group.id and waiter_member.id == supplicant.id:
            if waiter_message.asDisplay().isdigit() and int(
                waiter_message.asDisplay()
            ) <= len(history):
                return int(waiter_message.asDisplay()) - 1
            return False

    try:
        if not (response := await asyncio.wait_for(inc.wait(response_waiter), 60)):
            return await ariadne.sendGroupMessage(group, MessageChain("已取消本次操作"))
    except asyncio.TimeoutError:
        return await ariadne.sendGroupMessage(group, MessageChain("等待超时"))

    restore_list = [
        (await ariadne.getMember(group, member), before)
        for _, member, before, _ in history[response]
    ]
    await update_name_card(restore_list, backup=False)
    await ariadne.sendGroupMessage(
        group,
        MessageChain("已完成本次恢复操作"),
    )
