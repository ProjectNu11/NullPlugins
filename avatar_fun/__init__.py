from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    RegexMatch,
    ElementMatch,
    ElementResult,
    RegexResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library.depend.function_call import FunctionCall
from library.depend.switch import Switch
from .trash import trash
from .util import get_image, async_write_gif

saya = Saya.current()
channel = Channel.current()

channel.name("AvatarFunPic")
channel.author("SAGIRI-kawaii, nullqwertyuiop")
channel.description("一个可以生成头像相关趣味图的插件，在群中发送 `[摸|亲|贴|撕|丢|爬|精神支柱|吞] [@目标|目标qq|目标图片]` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True) @ "at1",
                    UnionMatch("垃圾探头") @ "func",
                    RegexMatch(r"[\n\r]", optional=True),
                    ElementMatch(Image, optional=True) @ "image",
                    ElementMatch(At, optional=True) @ "at2",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def avatar_fun_one_element(
    app: Ariadne,
    event: MessageEvent,
    func: RegexResult,
    at1: ElementResult,
    image: ElementResult,
    at2: ElementResult,
):
    if image.matched:
        assert isinstance(image.result, Image)
        image_bytes = await get_image(image.result)
    elif at1.matched and not at2.matched:
        assert isinstance(at1.result, At)
        image_bytes = await get_image(at1.result.target)
    elif at2.matched:
        assert isinstance(at2.result, At)
        image_bytes = await get_image(at2.result.target)
    else:
        image_bytes = await event.sender.get_avatar()
    func: str = func.result.display
    if not image_bytes:
        return
    composed = None
    if func == "垃圾探头":
        composed = await trash(image_bytes)
    if not composed:
        return
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain([Image(data_bytes=composed)]),
    )
