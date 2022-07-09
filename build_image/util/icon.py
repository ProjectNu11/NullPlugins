import asyncio
from pathlib import Path

import numpy as np
from PIL import Image


class IconUtil:
    def __int__(self):
        raise NotImplementedError("This class is not intended to be instantiated.")

    @classmethod
    def get_icon(
        cls, icon: str, size: tuple = None, color: tuple[int, int, int] = (63, 63, 63)
    ):
        """
        Get an icon from the assets/icons folder

        :param icon: Name of the icon, must be in the assets/icons folder
        :param size: Size of the icon
        :param color: Color of the icon
        :return: Image of the icon, may be transparent if icon is not found
        """

        path = Path(Path(__file__).parent.parent, "assets", "icons", f"{icon}.png")
        if not path.exists():
            return Image.new("RGBA", size, (0, 0, 0, 0))
        icon = Image.open(str(path))
        if size is not None:
            icon = icon.resize(size)
        icon = cls.replace_color(icon, color)
        return icon

    @classmethod
    async def async_get_icon(
        cls, icon: str, size: tuple = None, color: tuple[int, int, int] = (63, 63, 63)
    ):
        """
        Get an icon from the assets/icons folder

        :param icon: Name of the icon, must be in the assets/icons folder
        :param size: Size of the icon
        :param color: Color of the icon
        :return: Image of the icon, may be transparent if icon is not found
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.get_icon, icon, size, color)

    @staticmethod
    def replace_color(icon: Image.Image, color: tuple[int, int, int]):
        """
        Replace the color of the icon

        :param icon: Icon to replace the color
        :param color: Color to replace
        :return: Icon with the specified color
        """

        icon = icon.convert("RGBA")
        data = np.array(icon)
        red, green, blue, alpha = data.T
        black = (red == 0) & (blue == 0) & (green == 0)
        data[..., :-1][black.T] = color
        icon = Image.fromarray(data)
        return icon

    @classmethod
    async def async_replace_color(cls, icon: Image.Image, color: tuple[int, int, int]):
        """
        Replace the color of the icon

        :param icon: Icon to replace the color
        :param color: Color to replace
        :return: Icon with the specified color
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.replace_color, icon, color)

    @staticmethod
    def get_emoji(emoji: str | int, size: tuple[int, int] = None):
        """
        Get an emoji from the assets/emoji folder

        :param emoji: emoji or unicode code point, must be one character if is a string
        :param size: Size of the emoji
        :return: Image of the emoji, may be transparent if emoji is not found
        """

        if isinstance(emoji, str) and not emoji.isdigit():
            emoji = ord(emoji)
        path = Path(
            Path(__file__).parent.parent,
            "assets",
            "emoji",
            "image",
            f"{emoji}.png",
        )
        if not path.exists():
            return Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        emoji = Image.open(str(path))
        if not size:
            return emoji
        return emoji.resize(size)
