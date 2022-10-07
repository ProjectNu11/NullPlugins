from pathlib import Path

from PIL import Image

from module.avatar_fun.util import make_jpg_or_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "think_what")


def think_what(*data: Image.Image) -> bytes:
    frame = Image.open(assets_dir / "0.png")

    def make(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA").resize((int(img.width * 534 / img.height), 534))
        if img.width <= 493:
            img = img.resize((493, int(img.height * 493 / img.width)))
        img = img.crop((0, 0, 534, 493))
        base = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        base.paste(img, (530, 0), mask=img)
        base.paste(frame, mask=frame)
        return base

    return make_jpg_or_gif(data[-1], make)
