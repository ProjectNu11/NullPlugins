import hashlib
import asyncio

import contextlib
from io import BytesIO
from pathlib import Path

from graia.saya import Channel
from loguru import logger
from datetime import datetime, timedelta
from PIL import Image, ImageFont, ImageDraw

from library import config
from .strings import get_cut_str

font_file = Path(
    Path(__file__).parent.parent, "assets", "fonts", "sarasa-mono-sc-nerd-light.ttf"
)

try:
    font = ImageFont.truetype(str(font_file), 22)
except OSError as e:
    raise FileNotFoundError(f"Font file not found: {font_file}") from e

channel = Channel.current()

cache = Path(config.path.data, channel.module)
cache.mkdir(exist_ok=True, parents=True)


async def create_image(text: str, cut=64) -> bytes:
    return await asyncio.to_thread(_cache, text, cut)


def _cache(text: str, cut: int) -> bytes:
    str_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    cache.joinpath(str_hash[:2]).mkdir(exist_ok=True)
    cache_file = cache.joinpath(f"{str_hash[:2]}", f"{str_hash}.jpg")
    if cache_file.exists():
        logger.info(f"T2I Cache hit: {str_hash}")
    else:
        cache_file.write_bytes(_create_image(text, cut))

    return cache_file.read_bytes()


def _create_image(text: str, cut: int) -> bytes:
    cut_str = "\n".join(get_cut_str(text, cut))
    textx, texty = font.getsize_multiline(cut_str)
    image = Image.new("RGB", (textx + 40, texty + 40), (235, 235, 235))
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), cut_str, font=font, fill=(31, 31, 33))
    imageio = BytesIO()
    image.save(
        imageio,
        format="JPEG",
        quality=90,
        subsampling=2,
        qtables="web_high",
    )
    return imageio.getvalue()


async def delete_old_cache():
    cache_files = cache.glob("**/*")
    i = 0
    r = 0
    for cache_file in cache_files:
        i += 1
        if cache_file.stat().st_mtime < (
            (datetime.now() - timedelta(days=14)).timestamp()
        ):
            cache_file.unlink()
            with contextlib.suppress(OSError):
                cache_file.parent.rmdir()
            r += 1
    return i, r
