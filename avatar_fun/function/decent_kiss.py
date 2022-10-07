from pathlib import Path

from PIL import Image

from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "decent_kiss")


def decent_kiss(*data: Image.Image) -> bytes:
    upper = Image.open(assets_dir / "0.png")
    lower = Image.open(assets_dir / "1.png")

    def make(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA").resize((589, int(img.height * 589 / img.width)))
        base = Image.new(
            "RGBA",
            (589, upper.height + img.height + lower.height),
            (255, 255, 255, 255),
        )
        base.paste(upper, mask=upper)
        base.paste(img, (0, upper.height), mask=img)
        base.paste(lower, (0, upper.height + img.height), mask=lower)
        return base

    return make_jpg_or_gif(data[-1], make)
