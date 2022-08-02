from PIL import Image
from PIL.Image import Resampling

from library.image import TextUtil, ImageUtil
from module.avatar_fun.util import make_jpg_or_gif


def always(*data: Image.Image) -> bytes:
    def make(img: Image.Image) -> Image.Image:
        img_big = img.resize((500, img.height * 500 // img.width), Resampling.LANCZOS)
        img_small = img.resize((100, img.height * 100 // img.width), Resampling.LANCZOS)
        h1 = img_big.height
        h2 = max(img_small.height, 80)
        frame = Image.new("RGBA", (500, h1 + h2 + 10), "white")
        try:
            frame.paste(img_big, mask=img_big)
            frame.paste(
                img_small, (290, h1 + 5 + (h2 - img_small.height) // 2), mask=img_small
            )
        except ValueError:
            frame.paste(img_big)
            frame.paste(img_small, (290, h1 + 5 + (h2 - img_small.height) // 2))
        font = ImageUtil.get_font(60)
        left = TextUtil.render_text("要我一直", (0, 0, 0), font)
        left.resize((260, left.height * 260 // left.width), Resampling.LANCZOS)
        right = TextUtil.render_text("吗", (0, 0, 0), font)
        right.resize((80, right.height * 80 // right.width), Resampling.LANCZOS)
        frame.paste(left, (20, h1 + 5), mask=left)
        frame.paste(right, (400, h1 + 5), mask=right)
        return frame

    return make_jpg_or_gif(data[-1], make)
