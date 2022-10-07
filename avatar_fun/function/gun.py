from pathlib import Path

from PIL import Image

from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "gun")


def gun(*data: Image.Image) -> bytes:
    _gun = Image.open(assets_dir / "0.png")

    def make(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA")
        __gun = _gun.resize(
            (_gun.width * img.height * 2 // 3 // _gun.height, img.height * 2 // 3)
        )
        img.paste(
            __gun, (img.width - __gun.width, img.height - __gun.height), mask=__gun
        )
        return img

    return make_jpg_or_gif(data[-1], make)
