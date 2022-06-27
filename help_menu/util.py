import asyncio
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont
from graia.saya import Channel

from library import config
from library.util.switch import switch
from module import modules
from module.build_image.util import ImageUtil, IconUtil
from module.build_image.util.text import TextUtil

channel = Channel.current()


class HelpMenu:
    __field: int
    __y: int
    __boarder: int
    __space_size: Tuple[int, int]
    __canvas_width: int
    __canvas_height: int
    __avatar: Image.Image
    __round_avatar: Image.Image
    __mask: Image.Image
    __draw: ImageDraw
    __font: FreeTypeFont
    __composed: Image.Image

    def __init__(self, field: int, avatar: BytesIO):
        self.__field = field
        self.__avatar = Image.open(avatar)
        self.__y = 0
        self.__boarder = 20
        self.__canvas_width = 720
        self.__canvas_height = 99999
        self.__font = ImageUtil.get_font(30)
        self.__space_size = self.__font.getsize("\u3000")
        self.__mask = Image.new(
            "RGBA", (self.__canvas_width, self.__canvas_height), (0, 0, 0, 0)
        )
        self.__draw = ImageDraw.Draw(self.__mask)

    def __compose_avatar(self):
        avatar_size = 192
        resized_avatar = self.__avatar.resize((avatar_size, avatar_size))
        round_avatar = ImageUtil.add_blurred_shadow(
            ImageUtil.crop_to_circle(resized_avatar), radius=25, opacity=100
        )
        self.__round_avatar = round_avatar
        self.__y = self.__boarder
        self.__mask = ImageUtil.paste_to_center(self.__mask, round_avatar, y=self.__y)
        self.__y += round_avatar.height

    def __compose_description(self):
        if not (description := config.get_module_config(channel.module, "description")):
            return
        text = TextUtil.render_text(
            description,
            width=480,
            color=(63, 63, 63),
            font=self.__font,
            align="center",
        )
        self.__mask = ImageUtil.paste_to_center(self.__mask, text, y=self.__y)
        self.__y += text.height + self.__boarder * 2
        self.__draw_line(
            spacing=2,
        )

    def __draw_line(self, spacing: int = 2):
        line_width = 3
        self.__draw.line(
            (
                self.__boarder * 5,
                self.__y,
                self.__mask.width - self.__boarder * 5,
                self.__y,
            ),
            fill=(191, 191, 191),
            width=line_width,
        )
        self.__y += line_width + self.__boarder * spacing

    def __compose_icons(self):
        icon_size = (64,) * 2
        icon_location_x = self.__boarder * 5
        loaded = sorted(
            modules.search(match_any=True, loaded=True), key=lambda x: x.pack
        )
        unloaded = sorted(
            modules.search(match_any=True, loaded=False), key=lambda x: x.pack
        )

        def get_switch(_pack: str):
            _switch = switch.get(_pack, group=self.__field)
            if _switch is None:
                _switch = config.func.default
            return _switch

        icons = [
            "download-circle",
            "check-circle",
            "close-circle",
            "alert-circle",
            "help-circle",
            "!line!",
            *[
                "toggle-switch" if get_switch(module.pack) else "toggle-switch-off"
                for module in loaded
            ],
            "!line!",
            *[
                "toggle-switch" if get_switch(module.pack) else "toggle-switch-off"
                for module in unloaded
            ],
        ]
        icon_color = {"True": (102, 187, 106), "False": (183, 28, 28)}

        def get_icon_color(_pack: str):
            return icon_color.get(str(get_switch(_pack)))

        icons_properties = [
            {},
            {},
            {},
            {},
            {},
            {},
            *[{"color": get_icon_color(module.pack)} for module in loaded],
            {},
            *[{"color": get_icon_color(module.pack)} for module in unloaded],
        ]

        enabled = list(module.pack for module in modules if get_switch(module.pack))

        disabled = list(
            module.pack for module in modules if not get_switch(module.pack)
        )

        texts = [
            f"已安装 {len(modules)} 个插件",
            f"已启用 {len(enabled)} 个插件" if enabled else None,
            f"已禁用 {len(disabled)} 个插件" if disabled else None,
            f"未加载 {len(unloaded)} 个插件" if unloaded else None,
            f"帮助菜单仍在编写中...",
            "",
            *[module.name for module in loaded],
            "" if unloaded else None,
            *[module.name for module in unloaded],
        ]
        texts_properties = [
            {},
            {},
            {},
            {},
            {},
            {},
            *[{}] * len(loaded),
            {},
            *[{"color": (191, 191, 191)}] * len(unloaded),
        ]
        for icon, icon_property, text, text_property in zip(
            icons, icons_properties, texts, texts_properties
        ):
            if text is None:
                continue
            if icon == "!line!":
                self.__draw_line(
                    spacing=2,
                )
                continue
            icon = IconUtil.get_icon(icon, **{"size": icon_size, **icon_property})
            self.__mask.paste(icon, (icon_location_x, self.__y), mask=icon)
            text = TextUtil.render_text(
                text,
                **{
                    "width": self.__mask.width - icon_location_x - self.__boarder * 10,
                    "color": (63, 63, 63),
                    "font": self.__font,
                    "align": "left",
                    **text_property,
                },
            )
            self.__mask.paste(
                text,
                (
                    icon_location_x + icon_size[0] + self.__boarder * 2,
                    self.__y + icon.size[1] // 2 - int(self.__space_size[1] / 1.5),
                ),
                mask=text,
            )
            self.__y += max(icon.size[1], text.size[1]) + self.__boarder * 2

    def __compose(self):
        background = ImageUtil.blur(
            self.__avatar.resize(
                (max(self.__canvas_width, self.__y + self.__boarder * 3),) * 2
            ),
            50,
            boarder=False,
        )

        background = background.crop(
            (
                (background.width - self.__canvas_width) // 2,
                0,
                (background.width + self.__canvas_width) // 2,
                background.height,
            )
        )
        background = ImageUtil.draw_rectangle(
            img=background,
            x=self.__boarder,
            y=self.__round_avatar.height // 2 + self.__boarder * 2,
            end_x=self.__mask.width - self.__boarder,
            end_y=self.__y + self.__boarder * 2,
            color=(255, 255, 255),
            round_radius=10,
            shadow=True,
        )
        background.paste(self.__mask, (0, 0), mask=self.__mask)
        self.__composed = background

    def compose(self) -> bytes:
        self.__compose_avatar()
        self.__compose_description()
        self.__compose_icons()
        self.__compose()
        output = BytesIO()
        self.__composed.convert("RGB").save(output, format="JPEG")
        return output.getvalue()

    async def async_compose(self) -> bytes:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.compose)
