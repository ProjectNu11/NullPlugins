from io import BytesIO

from PIL import Image as PillowImage, ImageDraw, ImageChops


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
