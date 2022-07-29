import asyncio

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.event.mirai import (
    BotJoinGroupEvent,
    BotOnlineEvent,
    MemberJoinEvent,
    BotGroupPermissionChangeEvent,
    GroupNameChangeEvent,
    NudgeEvent,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    WildcardMatch,
    ElementMatch,
    ElementResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.depend import Blacklist
from .utils.config import config

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def chitung_bot_join_group_event_handler(app: Ariadne, event: BotJoinGroupEvent):
    await app.send_group_message(event.group, MessageChain(config.cc.joinGroupText))


@channel.use(ListenerSchema(listening_events=[BotOnlineEvent]))
async def chitung_bot_online_event_handler(app: Ariadne):
    for group_id in config.devGroupID:
        await app.send_group_message(group_id, MessageChain(config.cc.onlineText))
        await asyncio.sleep(1)


@channel.use(ListenerSchema(listening_events=[MemberJoinEvent]))
async def chitung_member_join_event_handler(app: Ariadne, event: MemberJoinEvent):
    await app.send_group_message(
        event.member.group, MessageChain(config.cc.welcomeText)
    )


@channel.use(ListenerSchema(listening_events=[BotGroupPermissionChangeEvent]))
async def chitung_bot_group_permission_change_event_handler(
    app: Ariadne, event: BotGroupPermissionChangeEvent
):
    await app.send_group_message(
        event.group, MessageChain(config.cc.permissionChangedText)
    )


@channel.use(ListenerSchema(listening_events=[GroupNameChangeEvent]))
async def chitung_group_name_change_event_handler(
    app: Ariadne, event: GroupNameChangeEvent
):
    await app.send_group_message(
        event.group, MessageChain(config.cc.groupNameChangedText)
    )


@channel.use(ListenerSchema(listening_events=[NudgeEvent]))
async def chitung_nudge_event_handler(app: Ariadne, event: NudgeEvent):
    if event.target != app.account or event.context_type != "group":
        return
    await app.send_nudge(event.supplicant, event.group_id)
    await app.send_group_message(event.group_id, MessageChain(config.cc.nudgeText))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(WildcardMatch(), ElementMatch(At) @ "at", WildcardMatch())
        ],
        decorators=[
            Blacklist.check(),
        ],
    )
)
async def chitung_nudge_at_handler(
    app: Ariadne, event: GroupMessage, at: ElementResult
):
    assert isinstance(at.result, At)
    if at.result.target != app.account:
        return
    await app.send_nudge(event.sender)
