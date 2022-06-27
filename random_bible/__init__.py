import asyncio
import os
import random
from hashlib import md5
from io import BytesIO
from pathlib import Path

from PIL import Image as PillowImage
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, At, Quote, Source
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    ElementResult,
    RegexMatch,
)
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl, Waiter
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch, FunctionCall

saya = Saya.current()
channel = Channel.current()

channel.name("ModuleManager")
channel.author("nullqwertyuiop")
channel.description("")

data_dir = Path(config.path.data) / channel.module
data_dir.mkdir(exist_ok=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("随机圣经")])],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def get_bible(ariadne: Ariadne, event: GroupMessage):
    group_dir = data_dir / str(event.sender.group.id)
    if group_dir.is_dir():
        if images := os.listdir(str(group_dir)):
            return await ariadne.send_group_message(
                event.sender.group,
                MessageChain([Image(path=group_dir / random.choice(images))]),
            )
    return await ariadne.send_group_message(event.sender.group, MessageChain("暂无本群圣经"))


waiting = set()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    FullMatch("上传圣经"),
                    RegexMatch(r"[\n\r]?", optional=True),
                    ElementMatch(Image, optional=True) @ "image",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def upload_bible(ariadne: Ariadne, event: GroupMessage, image: ElementResult):
    source = event.message_chain.get_first(Source)
    group_dir = data_dir / str(event.sender.group.id)

    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def image_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if (
            waiter_group.id == event.sender.group.id
            and waiter_member.id == event.sender.id
        ):
            if waiter_message.has(Image):
                return await waiter_message.get_first(Image).get_bytes()
            else:
                return False

    if image.matched:
        assert isinstance(image.result, Image)
        image_bytes = await image.result.get_bytes()
    else:
        try:
            if event.message_chain.get_first(Quote) and (
                await ariadne.get_message_from_id(
                    event.message_chain.get_first(Quote).id
                )
            ).message_chain.get(Image):
                image_bytes = (
                    await (
                        await ariadne.get_message_from_id(
                            event.message_chain.get_first(Quote).id
                        )
                    )
                    .message_chain.get_first(Image)
                    .get_bytes()
                )
            else:
                raise AttributeError()
        except (IndexError, AttributeError):
            if event.sender.id in waiting:
                return await ariadne.send_message(
                    event.sender.group, MessageChain("请等待上一次上传结束后再进行新的上传"), quote=source
                )
            try:
                await ariadne.send_message(
                    event.sender.group, MessageChain("请在 30 秒内发送要上传的圣经"), quote=source
                )
                image_bytes = await asyncio.wait_for(
                    InterruptControl(ariadne.broadcast).wait(image_waiter), 30
                )
                if not image_bytes:
                    await ariadne.send_group_message(
                        event.sender.group,
                        MessageChain("未检测到图片，请重新进行上传操作，本次上传结束"),
                        quote=source,
                    )
                    return
            except asyncio.TimeoutError:
                await ariadne.send_group_message(
                    event.sender.group, MessageChain("图片等待超时，上传结束"), quote=source
                )
                return
            finally:
                if event.sender.id in waiting:
                    waiting.remove(event.sender.id)
    group_dir.mkdir(exist_ok=True)
    PillowImage.open(BytesIO(image_bytes)).convert("RGB").save(
        group_dir / f"{md5(image_bytes).hexdigest()}.jpg"
    )
    await ariadne.send_group_message(
        event.sender.group, MessageChain("上传成功"), quote=source
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("本群圣经总数")])],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def get_bible_count(app: Ariadne, event: GroupMessage):
    group_dir = data_dir / str(event.sender.group.id)
    msg = "暂无本群圣经"
    if group_dir.is_dir():
        msg = f"本群共有圣经 {len(os.listdir(group_dir))} 条"
    await app.send_group_message(event.sender.group, MessageChain(msg))
