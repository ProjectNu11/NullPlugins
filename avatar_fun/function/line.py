from PIL import Image, ImageDraw

from module.avatar_fun.util import make_jpg_or_gif


def line(*data: str | Image.Image) -> bytes:
    layout: list[str] = [x for x in data if isinstance(x, str)]
    layout: str = layout[-1] if layout else "上"
    image: Image.Image = [x for x in data if isinstance(x, Image.Image)][-1]
    assert layout in {"左", "右", "上", "下"}, "布局必须是左、右、上或下"
    assert getattr(image, "is_animated", False), "图片必须是 GIF"

    frozen: Image.Image | None = None
    frame_count: int = image.n_frames
    frame_index: int = 1

    def freeze(img: Image.Image) -> Image.Image:
        nonlocal frozen
        nonlocal frame_index

        left, right, top, bottom = 0, 0, 0, 0
        line_left, line_top = 0, 0
        paste_left, paste_top = 0, 0

        img = img.convert("RGB")
        if frozen is None:
            frozen = Image.new("RGBA", img.size, (0, 0, 0, 0))

        if layout == "上":
            right = img.width
            bottom = int(img.height * (frame_index / frame_count))
            line_top = bottom
        elif layout == "下":
            right = img.width
            top = int(img.height * (1 - frame_index / frame_count))
            bottom = img.height
            line_top = top
            paste_top = top
        elif layout == "左":
            bottom = img.height
            right = int(img.width * (frame_index / frame_count))
            line_left = right
        else:
            bottom = img.height
            left = int(img.width * (1 - frame_index / frame_count))
            right = img.width
            line_left = left
            paste_left = left

        if line_left:
            line_loc = (line_left, 0, line_left, img.height)
        else:
            line_loc = (0, line_top, img.width, line_top)

        frozen_base = frozen.copy()
        frozen_base.paste(img.crop((left, top, right, bottom)), (paste_left, paste_top))
        frozen_base.paste(frozen, mask=frozen)
        frozen = frozen_base.copy()

        draw = ImageDraw.Draw(frozen_base)
        draw.line(line_loc, fill=(1, 254, 254), width=5)
        img.paste(frozen_base, mask=frozen_base)

        frame_index += 1

        return img

    return make_jpg_or_gif(image, freeze, gif_max_frames=frame_count)
