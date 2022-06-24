import functools
import traceback

import aiohttp
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

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
            return MessageChain(
                [
                    Image(
                        data_bytes=await create_image(
                            f"[{func.__name__} 运行时出现异常]\n"
                            f"异常类型：\n{type(e)}\n"
                            f"异常内容：\n{traceback.format_exc()}",
                            cut=120,
                        )
                    )
                ]
            )

    return wrapper
