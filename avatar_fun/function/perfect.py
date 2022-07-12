from pathlib import Path

from PIL import Image

from module.avatar_fun.util import write_jpg

assets_dir = Path(Path(__file__).parent.parent, "assets", "perfect")


def perfect(*images: Image.Image) -> Image:
    avatar = images[-1].convert("RGBA")
    base = Image.open(Path(assets_dir, "0.jpg"))
    avatar = avatar.resize((190, 190), Image.ANTIALIAS)
    base.paste(avatar, (206, 75))
    return write_jpg(base)
