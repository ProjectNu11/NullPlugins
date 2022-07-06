import re
from io import BytesIO

import aiohttp
from PIL import Image as PillowImage, ImageDraw, ImageChops
from aiohttp import ClientResponseError
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, At, Plain
from graia.ariadne.model import Member


def get_match_element(message: MessageChain) -> list[int | Image | At]:
    elements: list[int | Image | At] = [
        element for element in message.__root__ if isinstance(element, (Image, At))
    ]
    msg = message.include(Plain).display
    if matched := re.findall(r"(?<!\d)[1-9]\d{4,10}", msg):
        elements.extend(map(lambda x: int(x), matched))
    return elements


async def get_image(img: int | Image | Member) -> bytes:
    async with aiohttp.ClientSession() as session:
        if isinstance(img, int):
            async with session.get(
                url=f"https://q1.qlogo.cn/g?b=qq&nk={img}&s=640"
            ) as resp:
                return await resp.read()
        try:
            if isinstance(img, Image):
                return await img.get_bytes()
            return await img.get_avatar()
        except ClientResponseError:
            if isinstance(img, Member):
                return await get_image(img.id)
            img_id = img.id.split(".")[0][1:-1].replace("-", "")
            async with session.get(
                url=f"https://gchat.qpic.cn/gchatpic_new/0/1-1-{img_id}/0"
            ) as resp:
                return await resp.read()


async def get_element_image(message: MessageChain) -> list[PillowImage.Image]:
    return [
        PillowImage.open(BytesIO(await get_image(element)))
        for element in get_match_element(message)
    ]


def write_gif(
    frames: list[PillowImage.Image], delay: int | list[int], loop: bool = True
) -> bytes:
    with BytesIO() as f:
        frames[0].save(
            f,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=delay,
            optimize=True,
            loop=0 if loop else 1,
        )
        return f.getvalue()


def write_jpg(img: PillowImage.Image, quality=95) -> bytes:
    with BytesIO() as f:
        img.save(
            f,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling=2,
            qtables="web_high",
        )
        return f.getvalue()


def crop_to_circle(img: PillowImage.Image) -> PillowImage.Image:
    n_img = img.copy()
    big_size = (n_img.size[0] * 3, n_img.size[1] * 3)
    mask = PillowImage.new("L", big_size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + big_size, fill=255)
    mask = mask.resize(n_img.size, PillowImage.LANCZOS)
    mask = ImageChops.darker(mask, n_img.split()[-1])
    n_img.putalpha(mask)
    return n_img
