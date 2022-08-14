from pathlib import Path

from PIL import Image

from library.image import ImageUtil
from module.avatar_fun.util import write_jpg

assets_dir = Path(Path(__file__).parent.parent, "assets", "back_to_work")


def back_to_work(*data: Image.Image) -> bytes:
    frame = Image.open(Path(assets_dir, "0.png"))
    img = data[-1]
    img = ImageUtil.crop_to_rect(img)
    if img.height != 310:
        img = img.resize((img.width * 310 // img.height, 310))
    base = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    img = img.rotate(18, expand=True)
    base.paste(img, (40, 32))
    base.paste(frame, (0, 0), mask=frame)
    return write_jpg(base)
