import random

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    SpacePolicy,
    UnionMatch,
    WildcardMatch,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import config
from library.depend import Switch, FunctionCall, Interval
from module.drift_bottle.compose import (
    compose,
    compose_register_success,
    compose_bottle,
    compose_add_bottle_success,
    return_or_delete_bottle_success,
    reply_bottle_success,
    compose_my_stat,
    compose_error,
)
from module.drift_bottle.util import (
    register,
    get_bottle,
    add_bottle,
    update_bottle_status,
    update_bottle_view_times,
    get_reply,
    ban_user,
    get_user,
    user_keep_bottle,
    add_reply,
)

channel = Channel.current()
DRIFT_BOTTLE_COUNT_LIMIT = 10
DRIFT_BOTTLE_CHAR_LIMIT = 400


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                UnionMatch("捞", "写", "扔", "扔回", "丢弃", "注册", "回复", "查看", "我的") @ "func",
                UnionMatch("漂流瓶", "drift"),
                WildcardMatch() @ "content",
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
            Interval.check(
                channel.module,
                seconds=30,
                on_failure=MessageChain("冷却 {interval} 后才可继续操作"),
            ),
        ],
    )
)
async def drift_bottle(
    app: Ariadne, event: MessageEvent, func: RegexResult, content: RegexResult
):
    try:
        err_text = None
        supplicant = event.sender.id
        function = func.result.display
        content = content.result.display if content.matched else None
        assert func.matched, (
            f"未指定功能，可用的功能有："
            f"\n{config.func.prefix}捞漂流瓶"
            f"\n        -> 捞一个漂流瓶"
            f"\n{config.func.prefix}写漂流瓶 内容"
            f"\n        -> 写一个漂流瓶"
            f"\n{config.func.prefix}扔漂流瓶 内容"
            f"\n        -> 写一个漂流瓶"
            f"\n{config.func.prefix}扔回漂流瓶"
            f"\n        -> 将捞到的漂流瓶扔回（可被捞取）"
            f"\n{config.func.prefix}丢弃漂流瓶"
            f"\n        -> 将捞到的漂流瓶丢弃（不可被捞取）"
            f"\n{config.func.prefix}注册漂流瓶 昵称（可选）"
            f"\n        -> 注册漂流瓶，不可更改昵称"
            f"\n{config.func.prefix}回复漂流瓶 内容"
            f"\n        -> 在捞到的漂流瓶下回复"
            f"\n{config.func.prefix}查看漂流瓶"
            f"\n        -> 查看捞到的漂流瓶"
            f"\n{config.func.prefix}我的漂流瓶"
            f"\n        -> 查看自己的漂流瓶统计"
        )
        if function == "注册":
            user = await register(supplicant, content)
            image = await compose(compose_register_success, user)
            return await app.send_message(
                event.sender.group if isinstance(event, GroupMessage) else event.sender,
                MessageChain(Image(data_bytes=image)),
            )
        assert (
            user := await get_user(user_id=supplicant)
        ), f"你还没有注册漂流瓶，请先发送 {config.func.prefix}注册漂流瓶 昵称（可选） 进行注册"
        if function == "捞":
            assert user.kept_bottle == "", "你已经捞取了漂流瓶且未扔回或丢弃"
            assert len(bottle_list := await get_bottle()), "暂时没有漂流瓶可捞"
            bottle = random.choice(bottle_list)
            replies = await get_reply(bottle.id)
            await update_bottle_status(bottle.id, 1)
            await update_bottle_view_times(bottle.id)
            await user_keep_bottle(supplicant, bottle.id)
            image = await compose(compose_bottle, bottle, *replies)
        elif function in ("写", "扔"):
            assert content, "漂流瓶内容不得为空"
            assert (
                len(content) <= DRIFT_BOTTLE_CHAR_LIMIT
            ), f"漂流瓶内容不得超过 {DRIFT_BOTTLE_CHAR_LIMIT} 字"
            assert (
                len(await get_bottle(supplicant)) < DRIFT_BOTTLE_COUNT_LIMIT
            ), f"你扔出且未被回收的漂流瓶数超过上限（{DRIFT_BOTTLE_COUNT_LIMIT}）"
            bottle_id = await add_bottle(supplicant, content)
            image = await compose(compose_add_bottle_success, bottle_id)
        elif function in ("扔回", "丢弃"):
            assert user.kept_bottle, "你还没有捞取漂流瓶"
            bottle_id = user.kept_bottle
            if function == "扔回":
                await update_bottle_status(bottle_id, 0)
                deleted = False
            else:
                await update_bottle_status(bottle_id, 2)
                deleted = True
            await user_keep_bottle(supplicant, "")
            image = await compose(return_or_delete_bottle_success, bottle_id, deleted)
        elif function == "回复":
            assert user.kept_bottle, "你还没有捞取漂流瓶"
            assert content, "回复内容不得为空"
            assert (
                len(content) <= DRIFT_BOTTLE_CHAR_LIMIT
            ), f"回复内容不得超过 {DRIFT_BOTTLE_CHAR_LIMIT} 字"
            bottle_id = user.kept_bottle
            await update_bottle_status(bottle_id, 0)
            await user_keep_bottle(supplicant, "")
            reply_id = await add_reply(bottle_id, supplicant, content)
            image = await compose(reply_bottle_success, reply_id)
        elif function == "查看":
            assert user.kept_bottle, "你还没有捞取漂流瓶"
            bottle_id = user.kept_bottle
            bottle = await get_bottle(bottle_id=bottle_id)
            bottle = bottle[0]
            replies = await get_reply(bottle_id)
            image = await compose(compose_bottle, bottle, *replies)
        else:
            avatar = await event.sender.get_avatar()
            image = await compose(compose_my_stat, user, avatar)
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=image)),
        )
    except AssertionError as err:
        err_text = err.args[0]
    except Exception as err:
        err_text = str(err)
    if err_text:
        image = await compose(compose_error, err_text)
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=image)),
        )
