import base64
from datetime import datetime
from hashlib import md5
from typing import Union, List, Literal

from sqlalchemy import select

from library.orm import orm
from .pepper import pepper
from .table import ChatRecord, SendRecord


def get_salt(text: Union[str, int]) -> str:
    return md5(base64.b64encode(str(text).encode("utf-8"))).hexdigest()


def get_hash(salt: str, text: Union[int, str]) -> str:
    return md5((pepper + salt + str(text)).encode()).hexdigest()


def generate_pass(text: Union[int, str]) -> str:
    salt = md5(base64.b64encode(str(text).encode("utf-8"))).hexdigest()
    hashed = md5((pepper + salt + str(text)).encode()).hexdigest()
    return f"md5${pepper}${salt}${hashed}"


async def get_chat_record(
    query: List[Literal["id", "time", "field", "sender", "persistent_string", "seg"]],
    group: int = None,
    member: int = None,
    time_min: datetime = None,
    time_max: datetime = None,
    conditions: list = None,
):
    if group is None and member is None:
        return AttributeError("group or member must be filled")
    if not conditions:
        conditions = [
            (ChatRecord.sender == generate_pass(member)) if member else True,
            (ChatRecord.field == generate_pass(group)) if group else True,
            (ChatRecord.time > time_min) if time_min else True,
            (ChatRecord.time < time_max) if time_max else True,
        ]
    if fetch := await orm.fetchall(
        select(*[getattr(ChatRecord, column) for column in query]).where(*conditions)
    ):
        return fetch


async def get_send_record(
    query: List[Literal["id", "time", "target", "type", "persistant_string"]],
    target: int,
    supplicant_type: Literal["group", "friend", "unknown"],
    time_min: datetime = None,
    time_max: datetime = None,
    conditions: list = None,
):
    if not conditions:
        conditions = [
            (SendRecord.target == generate_pass(target)) if target else True,
            (SendRecord.type == supplicant_type) if supplicant_type else True,
            (SendRecord.time > time_min) if time_min else True,
            (SendRecord.time < time_max) if time_max else True,
        ]
    if fetch := await orm.fetchall(
        select(*[getattr(SendRecord, column) for column in query]).where(*conditions)
    ):
        return fetch
