from io import BytesIO

from aiohttp import ClientSession
from graia.amnesia.message import MessageChain
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ParamMatch,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import config, PrefixMatch
from .util import HelpMenu

channel = Channel.current()

if not config.get_module_config(channel.module):
    config.update_module_config(channel.module, {"description": None})


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
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
