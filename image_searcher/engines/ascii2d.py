import asyncio
from io import BytesIO
from pathlib import Path
from typing import Optional, BinaryIO

from PIL import Image as PillowImage
from PicImageSearch import Network, Ascii2D
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from library.image.oneui_mock.elements import OneUIMock, Column, Banner, GeneralBox
from module.image_searcher.utils import get_thumb, error_catcher

bovw = True
custom_cfg = []

ICON = PillowImage.open(Path(__file__).parent.parent / "icon.png")


@error_catcher
async def ascii2d_search(
    *_,
    proxies: Optional[str] = None,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None,
    **__,
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should offer url or file!")
    async with Network(proxies=proxies) as client:
        ascii2d = Ascii2D(client=client, bovw=bovw)
        if url:
            resp = await ascii2d.search(url=url)
        elif file:
            resp = await ascii2d.search(file=file)
        if not resp.raw:

            def compose() -> bytes:
                return OneUIMock(
                    Column(
                        Banner("Ascii2D 搜图", icon=ICON),
                        GeneralBox("服务器未返回内容", "无法搜索到该图片"),
                    )
                ).render_bytes()

            return MessageChain(Image(data_bytes=await asyncio.to_thread(compose)))

        resp = resp.raw[1]
        thumb = await get_thumb(resp.thumbnail, proxies)

        def compose() -> bytes:
            return OneUIMock(
                Column(
                    Banner("Ascii2D 搜图", icon=ICON),
                    PillowImage.open(BytesIO(thumb)),
                    GeneralBox("标题", resp.title)
                    .add("作者", resp.author)
                    .add("图像详情", resp.detail)
                    .add("链接", resp.url),
                )
            ).render_bytes()

        return MessageChain(Image(data_bytes=await asyncio.to_thread(compose)))
