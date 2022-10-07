import asyncio
import functools
from pathlib import Path

import aiohttp
from PIL import Image as PillowImage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from library.image.oneui_mock.elements import (
    OneUIMock,
    Banner,
    Column,
    GeneralBox,
    HintBox,
)

ICON = PillowImage.open(Path(__file__).parent / "icon.png")


async def get_thumb(url: str, proxy: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy) as resp:
            return await resp.read()


def error_catcher(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:

            return MessageChain(
                [
                    Image(
                        data_bytes=await OneUIMock(
                            Column(
                                Banner(
                                    func.__name__.replace("_", " ").title(), icon=ICON
                                ),
                                GeneralBox("运行搜索时出现异常", f"{e}"),
                                HintBox(
                                    "可以尝试以下解决方案",
                                    "检查依赖是否为最新版本",
                                    "检查服务器 IP 是否被封禁",
                                    "检查 API 是否有效",
                                    "检查网络连接是否正常",
                                ),
                            )
                        ).async_render_bytes()
                    )
                ]
            )

    return wrapper
