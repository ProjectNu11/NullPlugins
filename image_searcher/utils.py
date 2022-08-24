import asyncio
import functools
import traceback

import aiohttp
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from library.image.oneui_mock.elements import (
    OneUIMock,
    Banner,
    Column,
    GeneralBox,
    HintBox,
)
from module.build_image import create_image


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

            def compose_error() -> bytes:
                return OneUIMock(
                    Column(
                        Banner(func.__name__.replace("_", "").title()),
                        GeneralBox("运行搜索时出现异常", f"{e}"),
                        HintBox(
                            "可以尝试以下解决方案",
                            "检查依赖是否为最新版本",
                            "检查服务器 IP 是否被封禁",
                            "检查 API 是否有效",
                            "检查网络连接是否正常",
                        ),
                    )
                ).render_bytes()

            return MessageChain(
                [Image(data_bytes=await asyncio.to_thread(compose_error))]
            )

    return wrapper
