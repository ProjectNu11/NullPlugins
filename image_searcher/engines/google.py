import asyncio
from io import BytesIO
from typing import Optional, BinaryIO

from PIL import Image as PillowImage
from PicImageSearch import Network, Google
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from library.image.oneui_mock.elements import OneUIMock, Column, Banner, GeneralBox
from module.image_searcher.utils import get_thumb, error_catcher

custom_cfg = []


@error_catcher
async def google_search(
    *_,
    proxies: Optional[str] = None,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None,
    **__,
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should offer url or file!")
    async with Network(proxies=proxies) as client:
        google = Google(client=client)
        if url:
            resp = await google.search(url=url)
        elif file:
            resp = await google.search(file=file)
        if not resp.raw:

            def compose() -> bytes:
                return OneUIMock(
                    Column(Banner("Google 搜图"), GeneralBox("服务器未返回内容", "无法搜索到该图片"))
                ).render_bytes()

            return MessageChain(Image(data_bytes=await asyncio.to_thread(compose)))
        resp = resp.raw[2]
        thumb = await get_thumb(resp.thumbnail, proxies)

        def compose() -> bytes:
            return OneUIMock(
                Column(
                    Banner("Google 搜图"),
                    PillowImage.open(BytesIO(thumb)),
                    GeneralBox("标题", resp.title).add("链接", resp.url),
                )
            ).render_bytes()

        return MessageChain(Image(data_bytes=await asyncio.to_thread(compose)))
