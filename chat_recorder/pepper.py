import asyncio

from graia.saya import Channel
from sqlalchemy import select

from library.config import config
from library.orm import orm
from .table import ChatRecord

channel = Channel.current()


def __get_pepper() -> str | None:
    async def async_get_pepper() -> str | None:
        cursor = await orm.execute(select(ChatRecord.sender))
        if data := cursor.first():
            return data[0].split("$")[1]

    loop = asyncio.get_event_loop()
    _pepper = loop.run_until_complete(async_get_pepper())
    return _pepper


if (
    not (pepper := config.get_module_config(channel.module, "pepper"))
    or len(pepper) != 16
):
    if (pepper := __get_pepper()) is None:
        pepper = "".join(
            __import__("random")
            .SystemRandom()
            .choice(string.ascii_letters + string.digits)
            for _ in range(16)
            if (string := __import__("string"))
        )
    config.update_module_config(
        channel.module,
        {"pepper": pepper},
    )
