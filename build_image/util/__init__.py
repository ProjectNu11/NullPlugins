from PIL import Image, ImageDraw

from .icon import IconUtil
from .image import ImageUtil

if __name__ == "__main__":
    avatar = Image.open("avatar.jpg")
    avatar_size = 256
    round_avatar = ImageUtil.add_blurred_shadow(
        ImageUtil.crop_to_circle(avatar), 25
    ).resize((avatar_size, avatar_size))
    background = ImageUtil.blur(avatar, 50, boarder=False)
    background = background.crop((0, 0, 700, 1080))
    boarder = 20
    background = ImageUtil.draw_rectangle(
        img=background,
        x=boarder,
        y=round_avatar.height // 2 + boarder * 2,
        end_x=700 - boarder,
        end_y=1080 - boarder * 2,
        color=(255, 255, 255),
        round_radius=10,
        shadow=True,
    )
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
    font = ImageUtil.get_font(24)
    text_size = draw.textsize("Null 是一个服务于 Furry 群体的 QQ 机器人", font=font)
    text = Image.new("RGBA", text_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text)
    draw.text((0, 0), text="Null 是一个服务于 Furry 群体的 QQ 机器人", font=font, fill=(63, 63, 63))
    background = ImageUtil.paste_to_center(background, round_avatar, y=boarder * 2)
    background = ImageUtil.paste_to_center(
        background, text, y=boarder * 2 + round_avatar.height + boarder
    )
    background.show()
    IconUtil.get_icon("account.png").show()
