from pathlib import Path
from PIL import Image

from module.avatar_fun.util import write_jpg

assets_dir = Path(Path(__file__).parent.parent, "assets", "rip")


def rip(*images: Image.Image) -> bytes:
    base = images[-1].resize((400, 400), Image.LANCZOS)
    bg = Image.new("RGB", (1080, 804), "#ffffff")
    frame = Image.open(assets_dir / "0.png")
    tmp1 = base.rotate(24, expand=True)
    tmp2 = base.rotate(-11, expand=True)
    bg.paste(tmp1, (-5, 350))
    bg.paste(tmp2, (649, 310))
    bg.paste(frame, (0, 0), mask=frame)
    return write_jpg(bg)
