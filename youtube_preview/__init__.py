import re
from datetime import datetime

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, ForwardNode, Forward
from graia.ariadne.message.parser.twilight import Twilight, WildcardMatch, RegexMatch
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import config
from library.depend import Switch, FunctionCall, Blacklist
from .util import get_video_id, query

channel = Channel.current()

if not config.get_module_config(channel.module):
    config.update_module_config(channel.module, {"key": None})


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    WildcardMatch().flags(re.S),
                    RegexMatch(
                        r"((?:https?://)?(?:www\.)?youtube.com/watch\?v=([a-zA-Z\d_.-]{11}))|"
                        r"((?:https?://)?(?:www\.)?(youtu\.be/[a-zA-Z\d_.-]{11}))"
                    ),
                    WildcardMatch(),
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
async def twitter_preview(app: Ariadne, event: MessageEvent):
    if not (ids := await get_video_id(event.message_chain.display)):
        return
    response = await query(ids)
    if isinstance(response, bytes):
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=response)),
        )
    images = [await video.compose() for video in response.items]
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
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        msg_chain,
    )
