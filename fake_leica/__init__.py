import asyncio
import math
from io import BytesIO
from pathlib import Path

from PIL import Image as PillowImage
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, MessageEvent
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Quote, At
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    Twilight,
    ElementMatch,
    ElementResult,
    ArgumentMatch,
    ArgResult,
    UnionMatch,
)
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import Waiter, InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.saya.channel import Channel

from library import PrefixMatch
from library.depend import Switch, FunctionCall, Blacklist

channel = Channel.current()

DEVICES = {"三星": "samsung note20 ultra.png", "samsung": "samsung note20 ultra.png"}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    PrefixMatch,
                    UnionMatch("leica", "莱卡"),
                    ArgumentMatch("-d", "--device", type=str, optional=True) @ "device",
                    RegexMatch(r"[\n\r]?", optional=True),
                    ElementMatch(Image, optional=True) @ "image",
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
async def fake_leica(
    ariadne: Ariadne, event: MessageEvent, device: ArgResult, image: ElementResult
):
    if device.matched:
        device = DEVICES.get(device.result, "samsung note20 ultra.png")
    else:
        device = "samsung note20 ultra.png"
    path = Path(Path(__file__).parent, "assets", "footer", device)
    if image.matched:
        assert isinstance(image.result, Image)
        image_bytes = await image.result.get_bytes()
    else:
        try:
            assert (quote := event.message_chain.get(Quote))
            assert (original := await ariadne.get_message_from_id(quote[0].id))
            assert (img := original.message_chain.get(Image))
            image_bytes = await img[0].get_bytes()
        except (UnknownTarget, AssertionError):

            @Waiter.create_using_function(listening_events=[GroupMessage])
            async def image_waiter(
                waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
            ):
                if (
                    waiter_group.id == event.sender.group.id
                    and waiter_member.id == event.sender.id
                ):
                    return (
                        await images[0].get_bytes()
                        if (images := waiter_message.get(Image))
                        else False
                    )

            try:
                await ariadne.send_message(
                    event.sender.group, MessageChain("请在 30 秒内发送要处理的图片")
                )
                if not (
                    image_bytes := await asyncio.wait_for(
                        InterruptControl(ariadne.broadcast).wait(image_waiter), 30
                    )
                ):
                    await ariadne.send_group_message(
                        event.sender.group,
                        MessageChain("未检测到图片，请重新进行上传操作，本次上传结束"),
                    )
                    return
            except asyncio.TimeoutError:
                await ariadne.send_group_message(
                    event.sender.group, MessageChain("图片等待超时，上传结束")
                )
                return

    await ariadne.send_group_message(
        event.sender.group,
        MessageChain([Image(data_bytes=await async_compose(image_bytes, path))]),
    )


def compose(_image: bytes, _footer: Path) -> bytes:
    image = PillowImage.open(BytesIO(_image))
    footer = PillowImage.open(_footer)
    footer_width = image.width
    footer_height = math.ceil(footer.height * (image.width / footer.width))
    footer = footer.resize((footer_width, footer_height))
    composed = PillowImage.new(
        "RGB", (image.width, image.height + footer.height), "white"
    )
    composed.paste(image)
    composed.paste(footer, (0, image.height))
    output = BytesIO()
    composed.save(output, format="jpeg")
    return output.getvalue()


async def async_compose(_image: bytes, _footer: Path) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, compose, _image, _footer)
