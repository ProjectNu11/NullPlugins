from pathlib import Path

from PIL import Image

from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "point_at")


def point_at(*data: Image.Image) -> bytes:
    _point_at = Image.open(assets_dir / "0.png")

    def make(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA")
        __point_at = _point_at.resize(
            (
                _point_at.width * img.height // 2 // _point_at.height,
                img.height // 2,
            )
        )
        img.paste(__point_at, (0, img.height - __point_at.height), mask=__point_at)
        return img

    return make_jpg_or_gif(data[-1], make)
