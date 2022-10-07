from pathlib import Path

from PIL import Image

from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "rip")


def rip(*data: Image.Image) -> bytes:
    frame = Image.open(Path(assets_dir, "0.png"))

    def make(img: Image.Image) -> Image.Image:
        bg = Image.new("RGB", (1080, 804), "#ffffff")
        img = img.convert("RGBA").resize((400, 400), Image.LANCZOS)
        tmp1 = img.rotate(24, expand=True)
        tmp2 = img.rotate(-11, expand=True)
        bg.paste(tmp1, (-5, 350))
        bg.paste(tmp2, (649, 310))
        bg.paste(frame, (0, 0), mask=frame)
        return bg

    return make_jpg_or_gif(data[-1], make)
