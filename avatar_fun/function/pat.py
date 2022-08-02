from pathlib import Path
from PIL import Image

from module.avatar_fun.util import write_gif, crop_to_circle

locations = [
    (14, 20, 98, 98),
    (12, 33, 101, 85),
    (8, 40, 110, 76),
    (10, 33, 102, 84),
    (12, 20, 98, 98),
]

assets_dir = Path(Path(__file__).parent.parent, "assets", "pat")


def pat(*data: Image.Image) -> bytes:
    base = crop_to_circle(data[-1].convert("RGBA"))
    frames: list[Image.Image] = []
    for i in range(5):
        hand = Image.open(Path(assets_dir, f"{i}.png"))
        frame = Image.new("RGBA", hand.size, (255, 255, 255, 255))
        x, y, w, h = locations[i]
        tmp = base.resize((w, h), Image.LANCZOS)
        frame.paste(tmp, (x, y), mask=tmp)
        frame.paste(hand, mask=hand)
        frames.append(frame)
    return write_gif(frames, 60)
