import asyncio
from io import BytesIO
from typing import Union

import aiohttp
import imageio
from aiohttp import ClientResponseError
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, At


def get_match_element(message: MessageChain) -> list:
    return [element for element in message.__root__ if isinstance(element, (Image, At))]


async def get_image(img: Union[int, Image]) -> bytes:
    async with aiohttp.ClientSession() as session:
        if isinstance(img, int):
            async with session.get(
                url=f"https://q1.qlogo.cn/g?b=qq&nk={img}&s=640"
            ) as resp:
                return await resp.read()
        try:
            img_bytes = await img.get_bytes()
        except ClientResponseError:
            img_id = img.id.split(".")[0][1:-1].replace("-", "")
            async with session.get(
                url=f"https://gchat.qpic.cn/gchatpic_new/0/1-1-{img_id}/0"
            ) as resp:
                img_bytes = await resp.read()
        finally:
            return img_bytes


def write_gif(frames: list, fps: int) -> bytes:
    output = BytesIO()
    imageio.mimsave(output, frames, format="gif", fps=fps)
    return output.getvalue()


async def async_write_gif(frames: list, fps: int) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, write_gif, frames, fps)
