import asyncio
import re
from pathlib import Path

from PIL import Image as PillowImage
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.exception import AccountMuted, UnknownTarget, RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    WildcardMatch,
    UnionMatch,
    ArgumentMatch,
    ArgResult,
    RegexResult,
)
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from library import prefix_match, config
from library.depend import FunctionCall, Blacklist, Permission
from library.image.oneui_mock.elements import (
    Banner,
    Column,
    GeneralBox,
    OneUIMock,
    HintBox,
)
from library.model import UserPerm
from library.util.switch import switch

saya = Saya.current()
channel = Channel.current()

channel.name("Broadcast")
channel.author("nullqwertyuiop")
channel.description("广播")


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    UnionMatch("broadcast", "广播"),
                    ArgumentMatch("-t", "--title", type=str) @ "title",
                    ArgumentMatch("-s", "--skip-maintainer", action="store_true")
                    @ "skip_maintainer",
                    WildcardMatch().flags(re.S) @ "message",
                ]
            )
        ],
        decorators=[
            Blacklist.check(),
            FunctionCall.record(channel.module),
            Permission.require(
                permission=UserPerm.BOT_OWNER,
                on_failure=MessageChain("Permission denied."),
            ),
        ],
    )
)
async def broadcast(
    app: Ariadne,
    event: FriendMessage,
    title: ArgResult,
    skip_maintainer: ArgResult,
    message: RegexResult,
):
    title: str = title.result
    message: str = message.result.display
    skip_maintainer: bool = skip_maintainer.matched
    image = await generate_image(title, message, skip_maintainer)
    await app.send_friend_message(
        event.sender, MessageChain(Image(data_bytes=image), Plain("是否继续发送？（是/y/Y）"))
    )

    async def waiter(
        _event: FriendMessage,
    ):
        if _event.sender.id != event.sender.id:
            return
        if not (_plain := _event.message_chain.get(Plain)):
            return
        _msg = MessageChain(_plain).display
        return _msg in ("是", "y", "Y")

    try:
        if not await FunctionWaiter(waiter, [FriendMessage]).wait(60):
            return await app.send_friend_message(event.sender, MessageChain("已取消发送"))
    except asyncio.exceptions.TimeoutError:
        return await app.send_friend_message(event.sender, MessageChain("超时，已取消发送"))

    succeed = 0
    skip = 0
    failed = 0
    unknown = 0
    for group in await app.get_group_list():
        try:
            if skip_maintainer and list(
                filter(
                    lambda x: x.id in config.owners, await app.get_member_list(group)
                )
            ):
                logger.success(f"跳过发送 >>> {group.name}({group.id})")
                skip += 1
                continue
            if isinstance(_ := switch.get(channel.module, group), bool) and not _:
                logger.success(f"跳过发送 >>> {group.name}({group.id})")
                skip += 1
                continue
            await asyncio.sleep(1)
            logger.success(f"广播发送 >>> {group.name}({group.id})")
            await app.send_group_message(group, MessageChain(Image(data_bytes=image)))
            succeed += 1
        except (AccountMuted, UnknownTarget, RemoteException) as e:
            logger.error(e)
            failed += 1
        except Exception as e:
            logger.error(e)
            unknown += 1

    msg = [Plain(f"发送成功：{succeed}")]
    if skip:
        msg.append(Plain(f"\n跳过发送：{skip}"))
    if failed:
        msg.append(Plain(f"\n发送失败：{failed}"))
    if unknown:
        msg.append(Plain(f"\n未知错误：{unknown}"))

    await app.send_friend_message(
        event.sender,
        MessageChain(
            msg,
        ),
    )


async def generate_image(title: str, message: str, skip: bool) -> bytes:
    return await OneUIMock(
        Column(
            Banner(
                text="广播消息",
                icon=PillowImage.open(Path(__file__).parent / "icon.png"),
            ),
            GeneralBox(
                text=title,
                description=message,
            ),
            HintBox(
                *(
                    ["本消息由维护人员发送"]
                    + (["本消息仅发送至不包含任何维护人员的群组"] if skip else [])
                    + ["可通过禁用广播模块来拒收本消息"]
                )
            ),
        )
    ).async_render_bytes()
