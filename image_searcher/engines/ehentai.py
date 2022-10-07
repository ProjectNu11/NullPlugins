import asyncio
from io import BytesIO
from pathlib import Path
from typing import Optional, BinaryIO

from PIL import Image as PillowImage
from PicImageSearch import Network, EHentai
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from library.image.oneui_mock.elements import (
    OneUIMock,
    Column,
    Banner,
    GeneralBox,
    QRCodeBox,
)
from module.image_searcher.utils import get_thumb, error_catcher

custom_cfg = []

ICON = PillowImage.open(Path(__file__).parent.parent / "icon.png")


@error_catcher
async def ehentai_search(
    *_,
    proxies: Optional[str] = None,
    cookies: Optional[str] = None,
    ex: bool = False,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None,
    **__,
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should offer url or file!")
    if ex and not cookies:
        raise ValueError("If you use EXHentai Searcher, you should offer cookies!")
    async with Network(proxies=proxies, cookies=cookies) as client:
        ehentai = EHentai(client=client)
        if url:
            resp = await ehentai.search(url=url, ex=ex)
        elif file:
            resp = await ehentai.search(file=file, ex=ex)
        if not resp.raw:

            return MessageChain(
                Image(
                    data_bytes=await OneUIMock(
                        Column(
                            Banner(f"E{'x' if ex else '-'}Hentai 搜图", icon=ICON),
                            GeneralBox("服务器未返回内容", "无法搜索到该图片"),
                        )
                    ).async_render_bytes()
                )
            )

        resp = resp.raw[0]
        thumb = await get_thumb(resp.thumbnail, proxies)

        return MessageChain(
            Image(
                data_bytes=await OneUIMock(
                    Column(
                        Banner(f"E{'x' if ex else '-'}Hentai 搜图", icon=ICON),
                        PillowImage.open(BytesIO(thumb)),
                        GeneralBox("标题", resp.title)
                        .add("类别", resp.type)
                        .add("上传日期", resp.date)
                        .add("标签", " ".join([f"#{tag}" for tag in resp.tags]))
                        .add("链接", resp.url),
                        QRCodeBox(resp.url),
                    )
                ).async_render_bytes()
            )
        )
