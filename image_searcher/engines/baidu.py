import asyncio
from io import BytesIO
from pathlib import Path
from typing import Optional, BinaryIO

from PIL import Image as PillowImage
from PicImageSearch import Network, BaiDu
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from library.image.oneui_mock.elements import (
    OneUIMock,
    Column,
    GeneralBox,
    Banner,
    ProgressBar,
    QRCodeBox,
)
from module.image_searcher.utils import get_thumb, error_catcher

custom_cfg = []

ICON = PillowImage.open(Path(__file__).parent.parent / "icon.png")


@error_catcher
async def baidu_search(
    *_, url: Optional[str] = None, file: Optional[BinaryIO] = None, **__
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should offer url or file!")
    async with Network() as client:
        baidu = BaiDu(client=client)
        if url:
            resp = await baidu.search(url=url)
        elif file:
            resp = await baidu.search(file=file)
        if not resp.raw:

            return MessageChain(
                Image(
                    data_bytes=await OneUIMock(
                        Column(
                            Banner("百度 搜图", icon=ICON),
                            GeneralBox("服务器未返回内容", "无法搜索到该图片"),
                        )
                    ).async_render_bytes()
                )
            )

        resp = resp.raw[2]
        thumb = await get_thumb(resp.thumbnail, "")

        return MessageChain(
            Image(
                data_bytes=await OneUIMock(
                    Column(
                        Banner("百度 搜图", icon=ICON),
                        PillowImage.open(BytesIO(thumb)),
                        ProgressBar(resp.similarity, "相似度", f"{resp.similarity}%"),
                        GeneralBox("标题", resp.title).add("链接", resp.url),
                        QRCodeBox(resp.url),
                    )
                ).async_render_bytes()
            )
        )
