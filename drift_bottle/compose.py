import asyncio
from io import BytesIO
from typing import Callable

from PIL import Image

from library import config
from library.image.oneui_mock.elements import (
    Column,
    Banner,
    GeneralBox,
    OneUIMock,
    HintBox,
    Header,
)
from module.drift_bottle.model import DBUser, DBottle, DBReply


async def compose(func: Callable[[...], bytes], *args) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


def compose_error(err_text: str) -> bytes:
    column = Column()
    banner = Banner("漂流瓶")
    box = GeneralBox(text="运行时出现错误", description=err_text)
    hint = HintBox(
        "可用的功能有：",
        f"\n{config.func.prefix}捞漂流瓶\n    -> 捞一个漂流瓶",
        f"\n{config.func.prefix}写漂流瓶 内容\n    -> 写一个漂流瓶",
        f"\n{config.func.prefix}扔漂流瓶 内容\n    -> 写一个漂流瓶",
        f"\n{config.func.prefix}扔回漂流瓶\n    -> 将捞到的漂流瓶扔回（可被捞取）",
        f"\n{config.func.prefix}丢弃漂流瓶\n    -> 将捞到的漂流瓶丢弃（不可被捞取）",
        f"\n{config.func.prefix}回复漂流瓶 内容\n    -> 在捞到的漂流瓶下回复并扔回",
        f"\n{config.func.prefix}注册漂流瓶 昵称（可选）\n    -> 注册漂流瓶，不可更改昵称",
        f"\n{config.func.prefix}查看漂流瓶\n    -> 查看捞到的漂流瓶",
        f"\n{config.func.prefix}我的漂流瓶\n    -> 查看自己的漂流瓶统计",
    )
    column.add(banner, box, hint)
    mock = OneUIMock(column)
    return mock.render_bytes()


def compose_register_success(user: DBUser) -> bytes:
    column = Column()
    banner = Banner("漂流瓶")
    box = GeneralBox(text="注册成功", description=f"你的漂流瓶用户ID是: {user.id}")
    box.add(text="注册时间", description=user.register_time.strftime("%Y-%m-%d %H:%M:%S"))
    hint = HintBox(
        "可用的功能有：",
        f"\n{config.func.prefix}捞漂流瓶\n    -> 捞一个漂流瓶",
        f"\n{config.func.prefix}写漂流瓶 内容\n    -> 写一个漂流瓶",
        f"\n{config.func.prefix}扔漂流瓶 内容\n    -> 写一个漂流瓶",
        f"\n{config.func.prefix}扔回漂流瓶\n    -> 将捞到的漂流瓶扔回（可被捞取）",
        f"\n{config.func.prefix}丢弃漂流瓶\n    -> 将捞到的漂流瓶丢弃（不可被捞取）",
        f"\n{config.func.prefix}回复漂流瓶 内容\n    -> 在捞到的漂流瓶下回复并扔回",
        f"\n{config.func.prefix}注册漂流瓶 昵称（可选）\n    -> 注册漂流瓶，不可更改昵称",
        f"\n{config.func.prefix}查看漂流瓶\n    -> 查看捞到的漂流瓶",
        f"\n{config.func.prefix}我的漂流瓶\n    -> 查看自己的漂流瓶统计",
    )
    column.add(banner, box, hint)
    mock = OneUIMock(column)
    return mock.render_bytes()


def compose_add_bottle_success(bottle_id: str) -> bytes:
    column = Column()
    banner = Banner("漂流瓶")
    box = GeneralBox(text="成功丢出漂流瓶", description=f"漂流瓶ID: {bottle_id}")
    column.add(banner, box)
    mock = OneUIMock(column)
    return mock.render_bytes()


def compose_bottle(bottle: DBottle, *replies: DBReply) -> bytes:
    column = Column()
    banner = Banner("漂流瓶")
    box = GeneralBox(text=f"来自 {bottle.sender[:16]} 的漂流瓶", description=bottle.content)
    box.add(text="发送时间", description=bottle.time.strftime("%Y-%m-%d %H:%M:%S"))
    box.add(text="查看次数", description=str(bottle.view_times))
    box.add(text="漂流瓶 ID", description=str(bottle.id))

    reply_box = GeneralBox()

    replies = sorted(list(replies), key=lambda x: x.time, reverse=True)

    for index, reply in enumerate(replies):
        reply_box.add(
            text=f"#{index + 1} 来自 {reply.sender[:16]} 的回复",
            description=reply.content,
        )

    hint_box = HintBox(
        "可发送以下指令继续操作",
        f"\n{config.func.prefix}扔回漂流瓶\n    -> 将捞到的漂流瓶扔回（可被捞取）",
        f"\n{config.func.prefix}丢弃漂流瓶\n    -> 将捞到的漂流瓶丢弃（不可被捞取）",
        f"\n{config.func.prefix}回复漂流瓶 内容\n    -> 在捞到的漂流瓶下回复并扔回",
    )

    hint = HintBox("保证漂流瓶池的良性循环", f"建议使用 {config.func.prefix}扔回漂流瓶")

    column.add(banner, box, reply_box, hint_box, hint)
    mock = OneUIMock(column)
    return mock.render_bytes()


def reply_bottle_success(reply_id: str) -> bytes:
    column = Column()
    banner = Banner("漂流瓶")
    box = GeneralBox(text="成功回复漂流瓶", description=f"评论ID: {reply_id}")
    column.add(banner, box)
    mock = OneUIMock(column)
    return mock.render_bytes()


def compose_my_stat(me: DBUser, avatar: bytes) -> bytes:
    column = Column()
    banner = Banner("漂流瓶")
    header = Header(me.name[:16], "漂流瓶统计", Image.open(BytesIO(avatar)))
    box = GeneralBox(text="捞取漂流瓶数", description=str(me.view_count))
    box.add(text="扔回漂流瓶数", description=str(me.view_count - me.delete_count))
    box.add(text="丢弃漂流瓶数", description=str(me.delete_count))
    box.add(text="回复漂流瓶数", description=str(me.reply_count))
    column.add(banner, header, box)
    mock = OneUIMock(column)
    return mock.render_bytes()


def return_or_delete_bottle_success(bottle_id: str, deleted: bool) -> bytes:
    column = Column()
    banner = Banner("漂流瓶")
    box = GeneralBox(
        text=f"成功{'丢弃' if deleted else '扔回'}漂流瓶", description=f"漂流瓶ID: {bottle_id}"
    )
    column.add(banner, box)
    mock = OneUIMock(column)
    return mock.render_bytes()
