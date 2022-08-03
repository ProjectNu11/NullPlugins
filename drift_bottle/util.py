from datetime import datetime
from hashlib import md5

from sqlalchemy import select

from library.orm import orm
from module.drift_bottle.model import DBUser, DBottle, DBReply
from module.drift_bottle.table import DriftBottleUser, DriftBottle, DriftBottleReply


async def register(supplicant: int, name: str | None = None) -> DBUser | None:
    assert (
        _ := await get_user(user_id=supplicant)
    ) is None, (
        f"该用户已注册，ID 为 {_.id}，注册时间为 {_.register_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    if name:
        assert len(name) <= 16, "用户名长度不能超过 16 个字符"
    _supplicant = md5(str(supplicant).encode()).hexdigest()
    await orm.insert_or_update(
        DriftBottleUser,
        [DriftBottleUser.id == _supplicant],
        {
            "id": _supplicant,
            "name": name or _supplicant,
            "register_time": datetime.now(),
        },
    )
    return await get_user(user_id=supplicant)


async def get_user(*, user_id: int | str = None, name: str = None) -> DBUser | None:
    if user_id:
        if isinstance(user_id, int):
            user_id = md5(str(user_id).encode()).hexdigest()
        condition = [DriftBottleUser.id == user_id]
    elif name:
        condition = [DriftBottleUser.name == name]
    else:
        return None
    if user := await orm.fetchone(
        select(
            DriftBottleUser.id,
            DriftBottleUser.name,
            DriftBottleUser.register_time,
            DriftBottleUser.banned,
            DriftBottleUser.view_count,
            DriftBottleUser.reply_count,
            DriftBottleUser.delete_count,
            DriftBottleUser.kept_bottle,
        ).where(*condition)
    ):
        return DBUser(
            id=user[0],
            name=user[1],
            register_time=user[2],
            banned=user[3],
            view_count=user[4],
            reply_count=user[5],
            delete_count=user[6],
            kept_bottle=user[7],
        )


async def get_bottle(supplicant: int = None, bottle_id: str = None) -> list[DBottle]:
    if supplicant:
        condition = [
            DriftBottle.status == 0,
            DriftBottle.sender == md5(str(supplicant).encode()).hexdigest(),
        ]
    elif bottle_id:
        condition = [DriftBottle.id == bottle_id]
    else:
        condition = [DriftBottle.status == 0]
    if bottles := await orm.all(
        select(
            DriftBottle.id,
            DriftBottle.time,
            DriftBottle.sender,
            DriftBottle.content,
            DriftBottle.status,
            DriftBottle.view_times,
        ).where(*condition)
    ):
        return [
            DBottle(
                id=bottle[0],
                time=bottle[1],
                sender=bottle[2],
                content=bottle[3],
                status=bottle[4],
                view_times=bottle[5],
            )
            for bottle in bottles
        ]
    return []


async def add_bottle(supplicant: int, content: str) -> str:
    user = await get_user(user_id=supplicant)
    bottle_id = md5((user.id + str(datetime.now()) + content).encode()).hexdigest()
    await orm.insert_or_update(
        DriftBottle,
        [DriftBottle.id == bottle_id],
        {
            "id": bottle_id,
            "time": datetime.now(),
            "sender": user.name,
            "content": content,
            "status": 0,
            "view_times": 0,
        },
    )
    return bottle_id


async def update_bottle_status(bottle: str, status: int) -> None:
    await orm.insert_or_update(
        DriftBottle,
        [DriftBottle.id == bottle],
        {"status": status},
    )


async def user_keep_bottle(supplicant: int, kept_bottle: str) -> None:
    _user = md5(str(supplicant).encode()).hexdigest()
    await orm.insert_or_update(
        DriftBottleUser,
        [DriftBottleUser.id == _user],
        {"kept_bottle": kept_bottle},
    )


async def update_bottle_view_times(bottle: str) -> None:
    await orm.insert_or_update(
        DriftBottle,
        [DriftBottle.id == bottle],
        {"view_times": DriftBottle.view_times + 1},
    )


async def get_reply(bottle: str) -> list[DBReply]:
    if replies := await orm.all(
        select(
            DriftBottleReply.id,
            DriftBottleReply.bottle_id,
            DriftBottleReply.time,
            DriftBottleReply.sender,
            DriftBottleReply.content,
        ).where(DriftBottleReply.bottle_id == bottle)
    ):
        return [
            DBReply(
                id=reply[0],
                bottle_id=reply[1],
                time=reply[2],
                sender=reply[3],
                content=reply[4],
            )
            for reply in replies
        ]
    return []


async def add_reply(bottle: str, supplicant: int, content: str) -> str:
    user = await get_user(user_id=supplicant)
    reply_id = md5((user.id + str(datetime.now()) + content).encode()).hexdigest()
    await orm.insert_or_update(
        DriftBottleReply,
        [DriftBottleReply.id == reply_id],
        {
            "id": reply_id,
            "bottle_id": bottle,
            "time": datetime.now(),
            "sender": user.name,
            "content": content,
        },
    )
    return reply_id


async def ban_user(user: int) -> None:
    _user = md5(str(user).encode()).hexdigest()
    await orm.insert_or_update(
        DriftBottleUser,
        [DriftBottleUser.id == _user],
        {"banned": 1},
    )
