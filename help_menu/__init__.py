import pickle
from hashlib import md5
from io import BytesIO

from aiohttp import ClientSession
from graia.amnesia.message import MessageChain
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    SpacePolicy,
    ParamMatch,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from pydantic import BaseModel

from library import config
from library.util.switch import switch
from .util import HelpMenu
from .. import modules

channel = Channel.current()

if not config.get_module_config(channel.module):
    config.update_module_config(channel.module, {"description": None})


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                    FullMatch("help"),
                    ParamMatch(optional=True) @ "module",
                ]
            )
        ],
    )
)
async def help_menu(app: Ariadne, event: MessageEvent, module: RegexResult):
    if module.matched:
        _: str = module.result.as_display
    field = event.sender.group.id if isinstance(event, GroupMessage) else 0
    async with ClientSession() as session:
        async with session.get(
            f"https://q2.qlogo.cn/headimg_dl?dst_uin={app.account}&spec=640"
        ) as resp:
            avatar = BytesIO(await resp.read())
    menu = HelpMenu(field, avatar).compose()
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain([Image(data_bytes=menu)]),
    )
