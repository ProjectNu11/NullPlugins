import re
from datetime import datetime

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, ForwardNode, Forward
from graia.ariadne.message.parser.twilight import Twilight, WildcardMatch, RegexMatch
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

from library import config
from library.depend import Switch, FunctionCall
from .model.response import ErrorResponse
from .util import get_status_id, query

channel = Channel.current()

if not config.get_module_config(channel.module):
    config.update_module_config(channel.module, {"bearer": None})


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    WildcardMatch().flags(re.S),
                    RegexMatch(
                        r"((?:https?://)?(?:www\.)?twitter\.com/[\w\d]+/status/(\d+))|"
                        r"((?:https?://)?(?:www\.)?(t\.co/[a-zA-Z\d_.-]{10}))"
                    ),
                    WildcardMatch(),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
        ],
    )
)
async def twitter_preview(app: Ariadne, event: MessageEvent):
    if not (ids := await get_status_id(event.message_chain.display)):
        return
    response = await query(ids)
    if isinstance(response, bytes):
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=response)),
        )
    elif isinstance(response, ErrorResponse):
        images = [await error.compose() for error in response.errors]
        media = []
    else:
        parsed = response.parse()
        images = [await tweet.compose() for tweet in parsed]
        media: list[tuple[bytes, str]] = [
            await tweet.get_video_bytes() for tweet in parsed if tweet.has_video
        ]
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
    if media:
        for _media in media:
            data, name = _media
            try:
                await app.upload_file(
                    data=data,
                    target=event.sender.group
                    if isinstance(event, GroupMessage)
                    else event.sender,
                    name=name,
                )
            except RemoteException as err:
                logger.error(err)
                if "upload check_security fail" in str(err):
                    await app.send_message(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        MessageChain("文件未通过安全检查"),
                    )
