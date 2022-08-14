import asyncio
import random
from datetime import datetime

from dateutil.relativedelta import relativedelta
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.event.mirai import NudgeEvent
from graia.ariadne.exception import AccountMuted, UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.twilight import (
    MatchResult,
    Twilight,
    FullMatch,
    ElementMatch,
    RegexMatch,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from library import config, PrefixMatch
from library.depend import Switch, Blacklist, FunctionCall, Interval
from library.util.switch import switch

channel = Channel.current()

channel.name("Nudge")
channel.author("nullqwertyuiop")
channel.description("")

nudge_data = {}
nudged_data = {}
REFRESH_TIME = relativedelta(minutes=1)

NUDGE_ACTION = {
    1: [True, None],
    2: [True, "不许戳了！"],
    3: [True, "说了不许再戳了！"],
    4: [True, None],
    5: [True, "呜呜呜你欺负我，不理你了！"],
    10: [False, "你真的很有耐心欸。"],
}


@channel.use(ListenerSchema(listening_events=[NudgeEvent]))
async def nudged(app: Ariadne, event: NudgeEvent):
    if (
        event.target != config.account
        or event.supplicant == config.account
        or event.context_type != "group"
    ):
        return
    if (_ := switch.get(channel.module, event.group_id)) is None:
        if not config.func.default:
            return
    elif not _:
        return
    if not (member := await app.get_member(event.group_id, event.supplicant)):
        return
    logger.info(f"机器人被群 <{member.group.name}> 中用户 <{member.name}> 戳了戳。")
    await Interval.check_and_raise(channel.module, event.supplicant, seconds=5)
    times, last_run = nudged_data.get(event.supplicant, [1, datetime.fromtimestamp(0)])
    if last_run + REFRESH_TIME < datetime.now():
        times = 1
    send_nudge, message = NUDGE_ACTION.get(times, [False, None])
    try:
        if send_nudge:
            await app.send_nudge(member)
        if message:
            await app.send_group_message(member.group, MessageChain(message))
    except AccountMuted:
        logger.error(f"账号在群 <{member.group.name}> 中被禁言，无法发送")
    finally:
        nudged_data[event.supplicant] = [times + 1, datetime.now()]


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
                    FullMatch("戳"),
                    FullMatch("我", optional=True) @ "me",
                    ElementMatch(At, optional=True) @ "at",
                    RegexMatch(r"[1-9][0-9]*次", optional=True) @ "times",
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
async def nudge(
    app: Ariadne,
    group: Group,
    member: Member,
    me: MatchResult,
    at: MatchResult,
    times: MatchResult,
):
    try:
        assert me.matched or at.matched or times.matched, ""
        assert not (me.matched and at.matched), "到底戳谁？"
        assert me.matched or at.matched, "也不说要戳谁......"
        times = int(times.result.display[:-1]) if times.matched else 1
        assert times <= 10, "太多次啦！"
    except AssertionError as err:
        if err.args[0] == "":
            return
        return await app.send_group_message(group, MessageChain(err.args[0]))
    target = member if me.matched else await app.get_member(group, at.result.target)
    if not target:
        return
    count = 0
    if target.group.id not in nudge_data.keys():
        nudge_data[target.group.id] = {member.id: {"count": 0, "time": datetime.now()}}
    elif member.id not in nudge_data[target.group.id].keys():
        nudge_data[target.group.id][member.id] = {
            "count": 0,
            "time": datetime.now(),
        }
    else:
        period = nudge_data[target.group.id][member.id]["time"] + REFRESH_TIME
        if datetime.now() >= period:
            nudge_data[target.group.id][member.id] = {
                "count": 0,
                "time": datetime.now(),
            }
        count = nudge_data[target.group.id][member.id]["count"]
    if count >= 10 or count + times > 10:
        return await app.send_group_message(group, MessageChain("有完没完？"))
    for _ in range(times):
        try:
            await app.send_nudge(target)
        except UnknownTarget:
            return
        count += 1
        await asyncio.sleep(0.25 * random.randint(1, 5))
    nudge_data[target.group.id][member.id]["count"] = count
    nudge_data[target.group.id][member.id]["time"] = datetime.now()
