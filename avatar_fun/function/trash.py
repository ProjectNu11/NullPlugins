from pathlib import Path

from PIL import Image

from ..util import write_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "trash")
pos_data = [
    [0, (0, 0)],
    [1, (0, 0)],
    [2, (41, 41)],
    [3, (41, 31)],
    [4, (41, 32)],
    [5, (41, 34)],
    [6, (41, 33)],
    [7, (41, 33)],
    [8, (41, 33)],
    [9, (41, 33)],
    [10, (41, 33)],
    [11, (41, 33)],
    [12, (41, 33)],
    [13, (41, 33)],
    [14, (41, 33)],
    [15, (41, 31)],
    [16, (41, 28)],
    [17, (41, 33)],
    [18, (38, 49)],
    [19, (39, 69)],
    [20, (39, 68)],
    [21, (39, 68)],
    [22, (41, 70)],
    [23, (38, 70)],
    [24, (0, 0)],
]


def trash(*data: Image.Image) -> bytes:
    avatar = data[-1].resize((77, 77), Image.LANCZOS)
    frames: list[Image.Image] = []
    for index, position in pos_data:
        base = Image.open(Path(assets_dir, f"{index}.png"))
        if position == (0, 0):
            frames.append(base)
            continue
        bg = Image.new("RGB", base.size, "white")
        bg.paste(avatar, position)
        bg.paste(base, mask=base)
        frames.append(bg)
    return write_gif(frames, 40)
