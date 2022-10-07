from io import BytesIO
from typing import Callable

import aiohttp
from PIL import Image as PillowImage, ImageDraw, ImageChops
from aiohttp import ClientResponseError
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, At, Plain


def get_match_element(message: MessageChain) -> list[str | int | Image | At]:
    elements: list[str | int | Image | At] = []
    for element in message:
        if isinstance(element, (Image, At)):
            elements.append(element)
        elif isinstance(element, Plain):
            for part in element.display.split(" "):
                part = part.strip("\n")
                if not part:
                    continue
                if part.isdigit():
                    part = int(part)
                elements.append(part)
    return elements


async def get_image(img: int | Image | At) -> bytes | str:
    if isinstance(img, str):
        return img
    async with aiohttp.ClientSession() as session:
        if isinstance(img, At):
            img = img.target
        if isinstance(img, int):
            async with session.get(
                url=f"https://q1.qlogo.cn/g?b=qq&nk={img}&s=640"
            ) as resp:
                return await resp.read()
        try:
            return await img.get_bytes()
        except ClientResponseError:
            img_id = img.id.split(".")[0][1:-1].replace("-", "")
            async with session.get(
                url=f"https://gchat.qpic.cn/gchatpic_new/0/1-1-{img_id}/0"
            ) as resp:
                return await resp.read()


async def get_element_image(message: MessageChain) -> list[PillowImage.Image]:
    elements = []
    for element in get_match_element(message):
        if isinstance(element, str):
            elements.append(element)
        else:
            elements.append(PillowImage.open(BytesIO(await get_image(element))))
    return elements


def write_gif(
    frames: list[PillowImage.Image], duration: int | list[int], loop: bool = True
) -> bytes:
    with BytesIO() as f:
        frames[0].save(
            f,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            optimize=True,
            loop=0 if loop else 1,
        )
        return f.getvalue()


def write_jpg(img: PillowImage.Image, quality=95) -> bytes:
    img = img.convert("RGB")
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


def make_jpg_or_gif(
    image: PillowImage,
    func: Callable[[PillowImage.Image], PillowImage.Image],
    gif_zoom: float = 1,
    gif_max_frames: int = 50,
) -> bytes:
    if not getattr(image, "is_animated", False):
        return write_jpg(func(image))
    index = range(image.n_frames)
    ratio = image.n_frames / gif_max_frames
    duration = image.info["duration"] / 1000
    if ratio > 1:
        index = (int(i * ratio) for i in range(gif_max_frames))
        duration *= ratio
    frames = []
    for i in index:
        image.seek(i)
        new_img = func(image)
        frames.append(
            new_img.resize(
                (int(new_img.width * gif_zoom), int(new_img.height * gif_zoom))
            )
        )
    return write_gif(frames, duration)
