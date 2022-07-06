from graia.saya import Channel
from sqlalchemy import select
from tencentcloud.common import credential

from library.config import config
from library.orm import orm
from .table import ViolationCount

channel = Channel.current()


class TencentCredential:
    __cred: credential.Credential
    __valid: bool
    __error_count: int = 0

    def __init__(self, module: str):
        cfg = config.get_module_config(module)
        if not cfg:
            self.__valid = False
            return
        if not cfg.get("secret_id", None) or not cfg.get("secret_key", None):
            self.__valid = False
            return
        else:
            self.__cred = credential.Credential(cfg["secret_id"], cfg["secret_key"])
            self.__valid = True

    def invalidate(self):
        self.flush_error_count()
        self.__valid = False

    def is_valid(self):
        return self.__valid

    def get_credential(self):
        return self.__cred

    def get_error_count(self):
        return self.__error_count

    def flush_error_count(self):
        self.__error_count = 0

    def error_count_plus_one(self):
        self.__error_count += 1
        if self.__error_count > 50:
            self.invalidate()


tencent_credential = TencentCredential(channel.module)


async def get_violation_count(group_id: int, member_id: int) -> int:
    if fetch := await orm.fetchone(
        select(ViolationCount.count).where(
            ViolationCount.group_id == group_id,
            ViolationCount.member_id == member_id,
        )
    ):
        return fetch[0]
    return 0


async def update_violation_count(group_id: int, member_id: int) -> int:
    count = await get_violation_count(group_id, member_id)
    await orm.insert_or_update(
        ViolationCount,
        [ViolationCount.group_id == group_id, ViolationCount.member_id == member_id],
        {
            "group_id": group_id,
            "member_id": member_id,
            "count": count + 1,
        },
    )
    return count + 1
