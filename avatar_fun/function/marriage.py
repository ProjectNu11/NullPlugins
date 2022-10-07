from pathlib import Path

from PIL import Image

from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "marriage")


def marriage(*data: Image.Image) -> bytes:
    left = Image.open(assets_dir / "0.png")
    right = Image.open(assets_dir / "1.png")

    def make(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA").resize((int(img.width * 1080 / img.height), 1080))
        img.paste(left, mask=left)
        img.paste(right, (img.width - right.width, 0), mask=right)
        return img

    return make_jpg_or_gif(data[-1], make)
