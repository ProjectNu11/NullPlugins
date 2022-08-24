import asyncio
import contextlib
import copy
from datetime import datetime

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.exception import UnknownTarget, RemoteException, AccountMuted
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Forward, ForwardNode
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import config, PrefixMatch
from library.depend import Switch, Blacklist, FunctionCall
from library.image.oneui_mock.elements import (
    OneUIMock,
    Column,
    Banner,
    GeneralBox,
    HintBox,
)
from library.util.switch import switch
from module.rss import RSSUpdate, FeedFilter, QUERY_INTERVAL_MINUTES
from module.rss.feeds import get_feed_from_id, register_feed, unregister_feed
from module.twitter_preview import get_status_id, query, ErrorResponse

channel = Channel.current()

MAX_COUNT_PER_FIELD = 10
RSSHUB_ENTRYPOINT = "/twitter/user/{target}"

if not (__cfg := config.get_module_config(channel.module)):
    config.update_module_config(
        channel.module,
        {"rsshub": None},
    )
    BASE_URL = ""
else:
    BASE_URL = __cfg.get("rsshub", "")

RSSHUB_LINK = str(BASE_URL) + RSSHUB_ENTRYPOINT


@channel.use(
    ListenerSchema(
        listening_events=[RSSUpdate], decorators=[FeedFilter.check("Twitter")]
    )
)
async def twitter_rss_on_update(app: Ariadne, event: RSSUpdate):
    feed = event.feed
    items = sorted(event.items.items, key=lambda x: x.published, reverse=True)
    status_ids = await get_status_id(" ".join([item.link for item in items]))
    response = await query(status_ids)
    if isinstance(response, bytes):
        images = [response]
    elif isinstance(response, ErrorResponse):
        images = [await error.compose("Twitter 订阅") for error in response.errors]
    else:
        parsed = response.parse()
        images = [await item.compose(banner_text="Twitter 订阅") for item in parsed]
    if len(images) == 1:
        msg_chain = MessageChain(Image(data_bytes=images[0]))
    else:
        msg_chain = MessageChain(
            Forward(
                [
                    ForwardNode(
                        target=config.account,
                        name=f"{config.name}#{config.num}",
                        time=datetime.now(),
                        message=MessageChain([Image(data_bytes=image)]),
                    )
                    for image in images
                ]
            )
        )
    feed = copy.copy(feed)
    with contextlib.suppress(UnknownTarget, RemoteException, AccountMuted):
        for group in feed.groups:
            if (_ := switch.get(channel.module, group)) is None:
                if not config.func.default:
                    continue
            elif not _:
                continue
            await app.send_group_message(group, msg_chain)
            await asyncio.sleep(3)
        for friend in feed.friends:
            await app.send_friend_message(friend, msg_chain)
            await asyncio.sleep(3)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
                    FullMatch("取消", optional=True) @ "unsubscribe",
                    FullMatch("订阅推特"),
                    WildcardMatch() @ "target",
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
async def twitter_rss_on_msg(
    app: Ariadne, event: MessageEvent, unsubscribe: RegexResult, target: RegexResult
):
    try:
        assert (
            target := str(target.result) if target.matched else None
        ), "未输入需要订阅或取消订阅的账号"
        url = RSSHUB_LINK.format(target=target)
        if unsubscribe.matched:
            unregister_feed(
                url=url,
                group=event.sender.group.id
                if isinstance(event, GroupMessage)
                else None,
                friend=event.sender.id if isinstance(event, FriendMessage) else None,
            )
        else:
            assert (
                len(
                    feeds := get_feed_from_id(
                        group=event.sender.group.id
                        if isinstance(event, GroupMessage)
                        else None,
                        friend=event.sender.id
                        if isinstance(event, FriendMessage)
                        else None,
                    )
                )
                + 1
                <= MAX_COUNT_PER_FIELD
            ), f"当前聊天区域超出最大可订阅数量 ({MAX_COUNT_PER_FIELD})"
            async with Ariadne.service.client_session.get(
                url, proxy=config.proxy, timeout=10
            ) as response:
                assert response.status == 200, "无法获取该账号的 Feed"
            register_feed(
                "Twitter",
                target,
                url=url,
                group=event.sender.group.id
                if isinstance(event, GroupMessage)
                else None,
                friend=event.sender.id if isinstance(event, FriendMessage) else None,
            )

        def compose() -> bytes:
            if not (
                _feeds := get_feed_from_id(
                    group=event.sender.group.id
                    if isinstance(event, GroupMessage)
                    else None,
                    friend=event.sender.id
                    if isinstance(event, FriendMessage)
                    else None,
                )
            ):
                _feeds = []

            return OneUIMock(
                Column(
                    Banner("Twitter 订阅"),
                    GeneralBox(
                        f"已{'取消' if unsubscribe.matched else '完成'}订阅",
                        f"已{'取消' if unsubscribe.matched else ''}订阅用户 {target} 的推文",
                    ).add("当前更新频率", f"{QUERY_INTERVAL_MINUTES} 分钟"),
                    GeneralBox(
                        f"本群已订阅 {len(_feeds) + 1} 名用户",
                        "\n".join(
                            [feed.title.split(":")[-1] for feed in _feeds] + []
                            if unsubscribe.matched
                            else [target]
                        ),
                    ),
                )
            ).render_bytes()

        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain([Image(data_bytes=await asyncio.to_thread(compose))]),
        )

    except AssertionError as err:
        err_text = err.args[0]

        def compose_error() -> bytes:
            return OneUIMock(
                Column(
                    Banner("Twitter 订阅"),
                    GeneralBox("运行时出现异常", err_text),
                    HintBox(
                        "可以尝试以下解决方案",
                        "检查 RssHub 链接是由有效" "检查服务器 IP 是否被封禁",
                        "检查网络连接是否正常",
                        "检查对应用户是否存在",
                        "检查对应用户是否开启推文保护",
                    ),
                )
            ).render_bytes()

        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain([Image(data_bytes=await asyncio.to_thread(compose_error))]),
        )
