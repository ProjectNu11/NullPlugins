import asyncio
from io import BytesIO
from pathlib import Path

import numpy
from PIL import Image as PillowImage

from .util import async_write_gif


async def trash(image_bytes: bytes) -> bytes:
    pos_data = [
        [0, (0, 0)],
        [1, (0, 0)],
        [2, (41, 41)],
        [3, (41, 31)],
        [4, (41, 32)],
        [5, (41, 34)],
        [6, (41, 33)],
        [7, (41, 33)],
        [8, (41, 33)],
        [9, (41, 33)],
        [10, (41, 33)],
        [11, (41, 33)],
        [12, (41, 33)],
        [13, (41, 33)],
        [14, (41, 33)],
        [15, (41, 31)],
        [16, (41, 28)],
        [17, (41, 33)],
        [18, (38, 49)],
        [19, (39, 69)],
        [20, (39, 68)],
        [21, (39, 68)],
        [22, (41, 70)],
        [23, (38, 70)],
        [24, (0, 0)],
    ]
    avatar = PillowImage.open(BytesIO(image_bytes)).convert("RGBA")
    avatar = avatar.resize((77, 77))

    def compose():
        __frames = []
        for __index, __position in pos_data:
            __base = PillowImage.open(
                Path(__file__).parent / "assets" / "trash" / f"{__index}.png"
            )
            if __position == (0, 0):
                __frames.append(numpy.array(__base))
                continue
            __bg = PillowImage.new("RGB", __base.size, "white")
            __bg.paste(avatar, __position)
            __bg.paste(__base, (0, 0), mask=__base)
            __frames.append(numpy.array(__bg))
        return __frames

    loop = asyncio.get_event_loop()
    image_frames = await loop.run_in_executor(None, compose)
    image = await async_write_gif(image_frames, 25)
    return image
