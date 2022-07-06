from pathlib import Path

from PIL import Image

from module.avatar_fun.util import write_gif

seq = [
    0,
    1,
    2,
    3,
    1,
    2,
    3,
    0,
    1,
    2,
    3,
    0,
    0,
    1,
    2,
    3,
    0,
    0,
    0,
    0,
    4,
    5,
    5,
    5,
    6,
    7,
    8,
    9,
]
locs = [(11, 73, 106, 100), (8, 79, 112, 96)]

assets_dir = Path(Path(__file__).parent.parent, "assets", "beat")


def beat(*images: Image.Image) -> bytes:
    base = images[-1]
    img_frames: list[Image.Image] = []
    for i in range(10):
        frame = Image.new("RGBA", (235, 196), "#ffffff")
        bg = Image.open(Path(assets_dir, f"{i}.png"))
        x, y, w, h = locs[1] if i == 2 else locs[0]
        frame.paste(base.resize((w, h)), (x, y))
        frame.paste(bg, (0, 0), mask=bg)
        img_frames.append(frame)
    frames = [img_frames[n] for n in seq]
    return write_gif(frames, 85)
