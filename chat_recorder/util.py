import base64
from datetime import datetime
from hashlib import md5
from typing import Literal

from sqlalchemy import select

from library.orm import orm
from .pepper import pepper
from .table import ChatRecord, SendRecord


def __get_salt(text: str | int) -> str:
    return md5(base64.b64encode(str(text).encode("utf-8"))).hexdigest()


def __get_hash(salt: str, text: int | str) -> str:
    return md5((pepper + salt + str(text)).encode()).hexdigest()


def generate_pass(text: int | str) -> str:
    salt = md5(base64.b64encode(str(text).encode("utf-8"))).hexdigest()
    hashed = md5((pepper + salt + str(text)).encode()).hexdigest()
    return f"md5${pepper}${salt}${hashed}"


async def get_chat_record(
    query: list[Literal["id", "time", "field", "sender", "persistent_string", "seg"]],
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
    if fetch := await orm.all(
        select(*[getattr(ChatRecord, column) for column in query]).where(*conditions)
    ):
        return fetch


async def get_send_record(
    query: list[Literal["id", "time", "target", "type", "persistant_string"]],
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
    if fetch := await orm.all(
        select(*[getattr(SendRecord, column) for column in query]).where(*conditions)
    ):
        return fetch
