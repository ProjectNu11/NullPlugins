from pathlib import Path

from PIL import Image

from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "perfect")


def perfect(*data: Image.Image) -> Image:
    base = Image.open(Path(assets_dir, "0.jpg"))

    def make(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA").resize((190, 190), Image.ANTIALIAS)
        _base = base.copy()
        _base.paste(img, (206, 75), mask=img)
        return _base

    return make_jpg_or_gif(data[-1], make)
