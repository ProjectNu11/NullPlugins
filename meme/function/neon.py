from pathlib import Path

from PIL import Image

from module.build_image.util import ImageUtil
from module.build_image.util.text import TextUtil
from ..util import write_gif

assets_dir = Path(Path(__file__).parent.parent, "assets", "neon")
yellow = (255, 240, 0)
purple = (118, 0, 200)
black = (0, 0, 0)
white = (255, 255, 255)


def neon(string: str) -> bytes:
    font = ImageUtil.get_font(24, "SourceHanSans-VF.ttf", "Heavy")
    black_text = TextUtil.render_text(text=string, color=black, font=font)
    white_text = TextUtil.render_text(text=string, color=white, font=font)
    yellow_right = Image.open(Path(assets_dir, "yellow.png"))
    purple_right = Image.open(Path(assets_dir, "purple.png"))
    right_size = (
        yellow_right.width * (black_text.height + 20) // yellow_right.height,
        black_text.height + 20,
    )
    yellow_right = yellow_right.resize(right_size, Image.LANCZOS)
    purple_right = purple_right.resize(right_size, Image.LANCZOS)
    size = (black_text.width + yellow_right.width + 20, black_text.height + 20)
    yellow_img = Image.new("RGBA", size, (*yellow, 255))
    purple_img = Image.new("RGBA", size, (*purple, 255))
    yellow_img.paste(black_text, (10, 10), mask=black_text)
    purple_img.paste(white_text, (10, 10), mask=white_text)
    yellow_img.paste(yellow_right, (black_text.width + 20, 0))
    purple_img.paste(purple_right, (black_text.width + 20, 0))
    return write_gif([yellow_img, purple_img], 100)
