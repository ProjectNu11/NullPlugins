import contextlib

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source, FlashImage, Plain, At
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import get_module_config, update_module_config
from library.depend import Switch
from module.content_moderation.image import run_image_moderation
from module.content_moderation.util import update_violation_count, TencentCredential

saya = Saya.current()
channel = Channel.current()

channel.name("ContentModeration")
channel.author("nullqwertyuiop")
channel.description("")


if not get_module_config(channel.module):
    update_module_config(
        channel.module,
        {"secret_id": None, "secret_key": None, "server": "ap-guangzhou"},
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[Switch.check(channel.module)]
    )
)
async def image_moderation(app: Ariadne, event: GroupMessage):
    if not (
        images := (event.messageChain.get(FlashImage) or event.messageChain.get(Image))
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
        await app.sendGroupMessage(
            event.sender.group,
            MessageChain.create(
                [
                    At(event.sender),
                    Plain(f" 你发送的图片未通过内容审核，已被记录 {count} 次\n"),
                    Plain(f"本次记录的原因：{sub_label}"),
                ]
            ),
        )
        with contextlib.suppress(PermissionError):
            await app.recallMessage(event.messageChain.getFirst(Source))
