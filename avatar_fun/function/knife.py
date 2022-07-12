from pathlib import Path

from PIL import Image

from module.avatar_fun.util import write_jpg, crop_to_circle

assets_dir = Path(Path(__file__).parent.parent, "assets", "knife")


def knife(*images: Image.Image) -> Image:
    back = Image.open(Path(assets_dir, "back.png")).convert("RGBA")
    mask = Image.open(Path(assets_dir, "mask.png")).convert("RGBA")
    left = crop_to_circle(
        images[-1].convert("RGBA").resize((175, 175), Image.LANCZOS)
    ).rotate(45)
    right = crop_to_circle(
        images[0 if len(images) == 1 else -2].convert("RGBA")
    ).resize((275, 275), Image.LANCZOS)
    back.paste(left, (1, 346), mask=left)
    back.paste(right, (107, 70), mask=right)
    back.paste(mask, mask=mask)
    return write_jpg(back)
