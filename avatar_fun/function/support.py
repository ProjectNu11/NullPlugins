from pathlib import Path

from PIL import Image
from PIL.Image import Resampling

from library.image import ImageUtil
from module.avatar_fun.util import write_jpg

assets_dir = Path(Path(__file__).parent.parent, "assets", "support")


def support(*data: Image.Image) -> bytes:
    img = data[-1]
    img = img.convert("RGBA")
    img = ImageUtil.crop_to_rect(img)
    img = img.resize((815, 815), Resampling.LANCZOS)
    img = img.rotate(23, expand=True)
    frame = Image.open(Path(assets_dir, "0.png"))
    frame.paste(img, (-172, -17), mask=img)
    return write_jpg(frame)
