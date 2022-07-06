from pathlib import Path
from PIL import Image

from module.avatar_fun.util import write_gif, crop_to_circle

target_locations = [
    (39, 91, 75, 75),
    (49, 101, 75, 75),
    (67, 98, 75, 75),
    (55, 86, 75, 75),
    (61, 109, 75, 75),
    (65, 101, 75, 75),
]
self_locations = [
    (102, 95, 70, 80, 0),
    (108, 60, 50, 100, 0),
    (97, 18, 65, 95, 0),
    (65, 5, 75, 75, -20),
    (95, 57, 100, 55, -70),
    (109, 107, 65, 75, 0),
]

assets_dir = Path(Path(__file__).parent.parent, "assets", "tuotoi")


def tuotoi(*images: Image.Image) -> bytes:
    self_avatar = crop_to_circle(images[0].convert("RGBA"))
    target_avatar = crop_to_circle(images[-1].convert("RGBA"))
    frames: list[Image.Image] = []
    for i in range(6):
        frame = Image.open(Path(assets_dir, f"{i}.png")).convert("RGBA")
        x, y, w, h = target_locations[i]
        tmp_target = target_avatar.resize((w, h), Image.LANCZOS)
        frame.paste(tmp_target, (x, y), mask=tmp_target)
        x, y, w, h, angle = self_locations[i]
        tmp_self = (
            self_avatar.resize((w, h), Image.LANCZOS)
            .resize((w, h))
            .rotate(angle, expand=True)
        )
        frame.paste(
            tmp_self,
            (x, y),
            mask=tmp_self,
        )
        frames.append(frame)
    return write_gif(frames, 50)
