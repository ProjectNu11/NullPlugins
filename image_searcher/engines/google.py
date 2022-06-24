from typing import Optional, BinaryIO

from PicImageSearch import Network, Google
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain

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
            return MessageChain("Google 无搜索结果")
        resp = resp.raw[2]
        return MessageChain(
            [
                Plain("Google 搜索到以下结果：\n"),
                Image(data_bytes=await get_thumb(resp.thumbnail, proxies)),
                Plain(f"\n标题：{resp.title}\n"),
                Plain(f"链接：{resp.url}"),
            ]
        )
