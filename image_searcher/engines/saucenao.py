import asyncio
from io import BytesIO
from typing import Optional, BinaryIO

from PIL import Image as PillowImage
from PicImageSearch import Network, SauceNAO
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.saya import Channel

from library import config
from library.image.oneui_mock.elements import OneUIMock, Column, GeneralBox, Banner
from module.image_searcher.utils import get_thumb, error_catcher

custom_cfg = ["api_key"]
channel = Channel.current()


@error_catcher
async def saucenao_search(
    *_,
    proxies: Optional[str] = None,
    api_key: str = None,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None,
    **__,
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should give url or file!")
    if not api_key:
        if not (
            saucenao_cfg := config.get_module_config(channel.module, "saucenao")
        ) or not (api_key := saucenao_cfg.get("api_key")):
            raise ValueError("未配置 SauceNAO API Key")
    async with Network(proxies=proxies) as client:
        saucenao = SauceNAO(client=client, api_key=api_key)
        if url:
            resp = await saucenao.search(url=url)
        elif file:
            resp = await saucenao.search(file=file)
        if not resp.raw:

            def compose() -> bytes:
                return OneUIMock(
                    Column(Banner("SauceNAO 搜图"), GeneralBox("服务器未返回内容", "无法搜索到该图片"))
                ).render_bytes()

            return MessageChain(Image(data_bytes=await asyncio.to_thread(compose)))
        resp = resp.raw[0]
        thumb = await get_thumb(resp.thumbnail, proxies)

        def compose() -> bytes:
            return OneUIMock(
                Column(
                    Banner("SauceNAO 搜图"),
                    PillowImage.open(BytesIO(thumb)),
                    GeneralBox("标题", resp.title)
                    .add("相似度", f"{resp.similarity}%")
                    .add("作者", resp.author)
                    .add("Pixiv 图像 id", str(resp.pixiv_id))
                    .add("Pixiv 画师 id", str(resp.member_id))
                    .add("链接", resp.url),
                )
            ).render_bytes()

        return MessageChain(Image(data_bytes=await asyncio.to_thread(compose)))
