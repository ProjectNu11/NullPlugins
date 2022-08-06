import contextlib

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source, FlashImage, Plain, At
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from pydantic import BaseModel, root_validator

from library.config import config
from library.depend import Switch
from module.content_moderation.image import run_image_moderation
from module.content_moderation.util import (
    update_violation_count,
    ContentModeration,
    tencent_credential,
)

saya = Saya.current()
channel = Channel.current()

channel.name("ContentModeration")
channel.author("nullqwertyuiop")
channel.description("")


class ContentModerationConfig(BaseModel):
    from_pickle: bool = True
    secret_id: str = None
    secret_key: str = None
    server: str = "ap-guangzhou"

    @root_validator()
    def value_check(cls, values):
        if all(
            [
                values.get("from_pickle"),
                values.get("secret_id", None) is not None,
                values.get("secret_key", None) is not None,
            ]
        ):
            logger.warning(
                '"from_pickle" is True, "secret_id" and "secret_key" are not None'
            )
            logger.warning("Using secret_id and secret_key from config")
        return values


if not config.get_module_config(channel.module):
    config.update_module_config(
        channel.module,
        ContentModerationConfig(),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[Switch.check(channel.module, no_notice=True, log=False)],
    )
)
async def image_moderation(app: Ariadne, event: GroupMessage):
    if not tencent_credential.is_valid():
        return
    if not (
        images := (
            event.message_chain.get(FlashImage) or event.message_chain.get(Image)
        )
    ):
        return
    can_pass = True
    sub_label = ""
    for img in images:
        img_id = img.id.split(".")[0][1:-1].replace("-", "")
        img_bytes = await img.get_bytes()
        if not can_pass:
            break
        can_pass, sub_label = await run_image_moderation(img_id, img_bytes)
    if not can_pass:
        count = await update_violation_count(event.sender.group.id, event.sender.id)
        await app.send_group_message(
            event.sender.group,
            MessageChain(
                [
                    At(event.sender),
                    Plain(f" 你发送的图片未通过内容审核，已被记录 {count} 次\n"),
                    Plain(f"本次记录的原因：{sub_label}"),
                ]
            ),
        )
        with contextlib.suppress(PermissionError):
            await app.recall_message(event.message_chain.get_first(Source))
