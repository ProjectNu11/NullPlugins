from pathlib import Path

from PIL import Image
from PIL.Image import Resampling

from library.image import ImageUtil
from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "support")


def support(*data: Image.Image) -> bytes:
    frame = Image.open(Path(assets_dir, "0.png"))

    def make(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA")
        img = ImageUtil.crop_to_rect(img)
        img = img.resize((815, 815), Resampling.LANCZOS)
        img = img.rotate(23, expand=True)
        _frame = frame.copy()
        _frame.paste(img, (-172, -17), mask=img)
        return _frame

    return make_jpg_or_gif(data[-1], make)
