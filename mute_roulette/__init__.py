import asyncio
import random

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    ElementResult,
    ArgumentMatch,
    ArgResult,
)
from graia.ariadne.model import Group, Member, MemberPerm
from graia.broadcast.interrupt import Waiter, InterruptControl
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch, FunctionCall

saya = Saya.current()
channel = Channel.current()

channel.name("MuteRoulette")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(".轮盘"),
                    ArgumentMatch("-f", "--fast", action="store_true", optional=True)
                    @ "fast",
                    ArgumentMatch("-h", "--help", action="store_true", optional=True)
                    @ "get_help",
                    ElementMatch(At, optional=True) @ "at",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def mute_roulette(
    ariadne: Ariadne,
    event: GroupMessage,
    fast: ArgResult,
    get_help: ArgResult,
    at: ElementResult,
):
    if get_help.matched:
        return await ariadne.send_group_message(
            event.sender.group,
            MessageChain(
                "[轮盘禁言]\n"
                "每盘游戏初始装有 1 颗子弹，子弹与撞针均随机，"
                "撞针与子弹位于同一位置时将视为失败。\n"
                "每轮开始时将向后移动一次撞针位置，直至触发子弹。\n"
                f"每轮开始前，{config.name} 将会提醒本轮玩家，请注意查看。\n"
                "每盘游戏结束时将自动禁言败方。祝游玩愉快！"
            ),
        )
    if event.sender.group.account_perm == MemberPerm.Member:
        return await ariadne.send_group_message(
            event.sender.group, MessageChain(f"{config.name} 需要管理员权限才可进行轮盘禁言")
        )
    if not at.matched:
        return
    fast = fast.matched
    at = at.result
    assert isinstance(at, At)
    target = await ariadne.get_member(event.sender.group, at.target)
    mute = random.randint(1, 10)
    if target.id == event.sender.id:
        try:
            await ariadne.mute_member(event.sender.group, target, mute)
        except PermissionError:
            pass
        return await ariadne.send_group_message(
            event.sender.group, MessageChain("这是在干什么？")
        )
    await ariadne.send_group_message(
        event.sender.group,
        MessageChain(
            [
                At(target=target),
                Plain("，"),
                At(target=event.sender),
                Plain(f" 邀请您进行本次轮盘禁言，失败者将被禁言 {mute} 分钟\n" f'请在 30 秒内回复 "接受" 或者 "拒绝"'),
            ]
        ),
    )
    mute = mute * 60
    try:

        @Waiter.create_using_function([GroupMessage])
        async def invite_confirm_waiter(
            group: Group, member: Member, msg: MessageChain
        ):
            if (
                event.sender.group.id == group.id
                and target.id == member.id
                and msg.display in ("接受", "拒绝")
            ):
                return msg.display == "接受"

        if not await InterruptControl(ariadne.broadcast).wait(
            invite_confirm_waiter, timeout=30
        ):
            return await ariadne.send_group_message(
                event.sender.group, MessageChain("已取消本次轮盘禁言")
            )
    except asyncio.TimeoutError:
        return await ariadne.send_group_message(
            event.sender.group, MessageChain("超时，操作取消")
        )

    victim = None
    if not fast:
        await ariadne.send_group_message(
            event.sender.group,
            MessageChain('本局轮盘禁言已开始！\n发送 "开枪" 或 "砰" 开始'),
        )
        bullet = random.randint(0, 5)
        slot = random.randint(0, 5)
        order = [event.sender, target]
        for index in range(6):
            try:
                player = order[index % 2]
                await ariadne.send_group_message(
                    event.sender.group,
                    MessageChain([At(target=player), Plain("，该你了")]),
                )
                await InterruptControl(ariadne.broadcast).wait(
                    Shoot(event.sender.group, player), timeout=30
                )
                if bullet == slot:
                    victim = player
                    break
                slot = (slot + 1) % 6
            except asyncio.TimeoutError:
                return await ariadne.send_group_message(
                    event.sender.group, MessageChain("超时，操作取消")
                )
    else:
        victim = random.choice([event.sender, target])
    assert victim
    try:
        await ariadne.mute_member(event.sender.group, victim, mute)
    except PermissionError:
        pass
    await ariadne.send_group_message(
        event.sender.group, MessageChain(f"很可惜，{victim.name} 失败了")
    )


class Shoot(Waiter.create([GroupMessage])):
    def __init__(self, group: Group, member: Member):
        self.group = group.id
        self.member = member.id

    async def detected_event(self, group: Group, member: Member, message: MessageChain):
        if (
            self.group == group.id
            and self.member == member.id
            and message.display in ("开枪", "砰")
        ):
            return True
