from pathlib import Path
from PIL import Image

from module.avatar_fun.util import write_gif

target_avatar_locations = [
    (58, 90),
    (62, 95),
    (42, 100),
    (50, 100),
    (56, 100),
    (18, 120),
    (28, 110),
    (54, 100),
    (46, 100),
    (60, 100),
    (35, 115),
    (20, 120),
    (40, 96),
]
self_avatar_locations = [
    (92, 64),
    (135, 40),
    (84, 105),
    (80, 110),
    (155, 82),
    (60, 96),
    (50, 80),
    (98, 55),
    (35, 65),
    (38, 100),
    (70, 80),
    (84, 65),
    (75, 65),
]

assets_dir = Path(Path(__file__).parent.parent, "assets", "kiss")


def kiss(*images: Image.Image) -> bytes:
    self_avatar = images[0]
    target_avatar = images[-1]
    frames: list[Image.Image] = []
    for i in range(13):
        frame = Image.open(assets_dir / f"{i}.png")
        frame.paste(target_avatar, target_avatar_locations[i], mask=target_avatar)
        if self_avatar is not None:
            frame.paste(self_avatar, self_avatar_locations[i], mask=self_avatar)
        frames.append(frame)
    return write_gif(frames, 50)
