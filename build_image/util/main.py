import timeit

from PIL import Image, ImageDraw

from icon import IconUtil
from image import ImageUtil
from text import TextUtil

if __name__ == "__main__":
    rendered = []

    def t():
        avatar_size = 192
        boarder = 20
        avatar = Image.open("avatar.jpg")
        resized_avatar = avatar.resize((avatar_size, avatar_size))
        round_avatar = ImageUtil.add_blurred_shadow(
            ImageUtil.crop_to_circle(resized_avatar), radius=25, opacity=100
        )

        canvas_width = 720
        canvas_height = 1920
        mask = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        y = boarder
        mask = ImageUtil.paste_to_center(mask, round_avatar, y=y)
        y += round_avatar.height

        description = "Null 是一个服务于 Furry 群体的 QQ 机器人"
        font = ImageUtil.get_font(30)
        space_size = font.getsize("\u3000")
        draw = ImageDraw.Draw(mask)
        text = TextUtil.render_text(
            description,
            width=480,
            color=(63, 63, 63),
            font=font,
            align="center",
        )
        mask = ImageUtil.paste_to_center(mask, text, y=y)
        y += text.height + boarder * 2

        line_width = 3
        draw.line(
            (boarder * 5, y, mask.width - boarder * 5, y),
            fill=(191, 191, 191),
            width=line_width,
        )
        y += line_width + boarder * 2

        icon_size = (64,) * 2
        icon_location_x = boarder * 5
        icons = [
            "download-circle",
            "check-circle",
            "close-circle",
            "help-circle",
            "!line!",
            "",
        ]
        icons_properties = [{}, {}, {}, {}, {}, {}]
        texts = [
            "已安装 xxx 个插件",
            "已启用 xxx 个插件",
            "已禁用 xxx 个插件",
            "发送 .help 查看帮助",
            "",
            "...",
        ]
        texts_properties = [{}, {}, {}, {}, {}, {}]
        for icon, icon_property, text, text_property in zip(
            icons, icons_properties, texts, texts_properties
        ):
            if icon == "!line!":
                line_width = 3
                draw.line(
                    (boarder * 5, y, mask.width - boarder * 5, y),
                    fill=(191, 191, 191),
                    width=line_width,
                )
                y += line_width + boarder * 2
                continue
            if text is None:
                continue
            icon = IconUtil.get_icon(icon, **{"size": icon_size, **icon_property})
            mask.paste(icon, (icon_location_x, y), mask=icon)
            text = TextUtil.render_text(
                text,
                **{
                    "width": mask.width - icon_location_x - boarder * 10,
                    "color": (63, 63, 63),
                    "font": font,
                    "align": "left",
                    **text_property,
                },
            )
            mask.paste(
                text,
                (
                    icon_location_x + icon_size[0] + boarder,
                    y + icon.size[1] // 2 - int(space_size[1] / 1.5),
                ),
                mask=text,
            )
            y += max(icon.size[1], text.size[1]) + boarder * 2

        background = ImageUtil.blur(
            avatar.resize((max(canvas_width, y + boarder * 3),) * 2), 50, boarder=False
        )
        background = background.crop((0, 0, canvas_width, y + boarder * 3))
        background = ImageUtil.draw_rectangle(
            img=background,
            x=boarder,
            y=round_avatar.height // 2 + boarder * 2,
            end_x=mask.width - boarder,
            end_y=y + boarder * 2,
            color=(255, 255, 255),
            round_radius=10,
            shadow=True,
        )
        background.paste(mask, (0, 0), mask=mask)

        rendered.append(background)

    print(f"Render Time: {timeit.Timer(t).timeit(1)}s")

    for i, image in enumerate(rendered):
        image.show(str(i))
