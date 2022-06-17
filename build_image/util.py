import asyncio
import base64
import math
from io import BytesIO
from itertools import groupby
from pathlib import Path
from typing import Union, Tuple, Optional, Literal, List

from PIL import ImageFont, Image, ImageDraw, ImageFilter
from PIL.Image import Resampling
from PIL.ImageFont import FreeTypeFont

from .assets.emoji import emoji_list


class BuildImage:
    """
    快捷生成图片与操作图片的工具类
    """

    def __init__(
        self,
        w: int = 0,
        h: int = 0,
        paste_image_width: int = 0,
        paste_image_height: int = 0,
        color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]] = None,
        image_mode: Literal[
            "1",
            "CMYK",
            "F",
            "HSV",
            "I",
            "L",
            "LAB",
            "P",
            "RGB",
            "RGBA",
            "RGBX",
            "YCbCr",
        ] = "RGBA",
        font_size: int = 30,
        background: Union[Optional[str], bytes, BytesIO, Path, Image.Image] = None,
        font: Union[str, Path, FreeTypeFont] = Path(
            Path(__file__).parent, "assets", "fonts", "SourceHanSans-VF.ttf"
        ),
        font_variation: Optional[str] = None,
        ratio: float = 1,
        is_alpha: bool = False,
        plain_text: Optional[str] = None,
        font_color: Optional[Union[str, Tuple[int, int, int]]] = None,
    ):
        """
        参数：
            :param w: 自定义图片的宽度，w=0时为图片原本宽度
            :param h: 自定义图片的高度，h=0时为图片原本高度
            :param paste_image_width: 当图片做为背景图时，设置贴图的宽度，用于贴图自动换行
            :param paste_image_height: 当图片做为背景图时，设置贴图的高度，用于贴图自动换行
            :param color: 生成图片的颜色
            :param image_mode: 图片的类型
            :param font_size: 文字大小
            :param background: 打开图片的路径
            :param font: 字体，默认在 __file__.parent / "assets" / "fonts" 路径下
            :param ratio: 倍率压缩
            :param is_alpha: 是否背景透明
            :param plain_text: 纯文字文本
        """
        self.w = w
        self.h = h
        self.paste_image_width = paste_image_width
        self.paste_image_height = paste_image_height
        self.current_w = 0
        self.current_h = 0
        self.font = (
            font
            if isinstance(font, FreeTypeFont)
            else ImageFont.truetype(str(font), font_size)
        )
        if font_variation:
            self.font.set_variation_by_name(font_variation)
        elif b"Regular" in self.font.get_variation_names():
            self.font.set_variation_by_name("Regular")

        if not plain_text and not color:
            color = (255, 255, 255)
        self.background = background
        if not background:
            if plain_text:
                if not color:
                    color = (255, 255, 255, 0)
                ttf_w, ttf_h = self.getsize(plain_text)
                self.w = max(self.w, ttf_w)
                self.h = max(self.h, ttf_h)
            self.markImg = Image.new(image_mode, (self.w, self.h), color)
            self.markImg.convert(image_mode)
        elif isinstance(background, Image.Image):
            self.markImg = background
            self.w = background.width
            self.h = background.height
            self.markImg = self.markImg.resize((self.w, self.h), Resampling.LANCZOS)
        elif not w and not h:
            self.markImg = Image.open(background)
            w, h = self.markImg.size
            if ratio and ratio > 0 and ratio != 1:
                self.w = int(ratio * w)
                self.h = int(ratio * h)
                self.markImg = self.markImg.resize((self.w, self.h), Resampling.LANCZOS)
            else:
                self.w = w
                self.h = h
        else:
            self.markImg = Image.open(background).resize(
                (self.w, self.h), Resampling.LANCZOS
            )
        if is_alpha:
            array = self.markImg.load()
            for i in range(w):
                for j in range(h):
                    pos = array[i, j]
                    is_edit = sum(x > 240 for x in pos[:3]) == 3
                    if is_edit:
                        array[i, j] = (255, 255, 255, 0)
        self.draw = ImageDraw.Draw(self.markImg)
        self.size = self.w, self.h
        if plain_text:
            fill = font_color or (0, 0, 0)
            self.text((0, 0), plain_text, fill)
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self.loop = asyncio.get_event_loop()

    async def apaste(
        self,
        img: "BuildImage" or Image,
        pos: Tuple[int, int] = None,
        alpha: bool = False,
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            异步 贴图
        参数：
            :param img: 已打开的图片文件，可以为 BuildImage 或 Image
            :param pos: 贴图位置（左上角）
            :param alpha: 图片背景是否为透明
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        await self.loop.run_in_executor(None, self.paste, img, pos, alpha, center_type)

    def paste(
        self,
        img: "BuildImage" or Image,
        pos: Tuple[int, int] = None,
        alpha: bool = False,
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            贴图
        参数：
            :param img: 已打开的图片文件，可以为 BuildImage 或 Image
            :param pos: 贴图位置（左上角）
            :param alpha: 图片背景是否为透明
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        if center_type:
            if center_type not in ["center", "by_height", "by_width"]:
                raise ValueError(
                    "center_type must be 'center', 'by_width' or 'by_height'"
                )
            width, height = 0, 0
            if not pos:
                pos = (0, 0)
            if center_type == "center":
                width = int((self.w - img.w) / 2)
                height = int((self.h - img.h) / 2)
            elif center_type == "by_width":
                width = int((self.w - img.w) / 2)
                height = pos[1]
            elif center_type == "by_height":
                width = pos[0]
                height = int((self.h - img.h) / 2)
            pos = (width, height)
        if isinstance(img, BuildImage):
            img = img.markImg
        if self.current_w == self.w:
            self.current_w = 0
            self.current_h += self.paste_image_height
        if not pos:
            pos = (self.current_w, self.current_h)
        if alpha:
            try:
                self.markImg.paste(img, pos, img)
            except ValueError:
                img = img.convert("RGBA")
                self.markImg.paste(img, pos, img)
        else:
            self.markImg.paste(img, pos)
        self.current_w += self.paste_image_width

    def getsize(self, msg: str) -> Tuple[int, int]:
        """
        说明：
            获取文字在该图片 font_size 下所需要的空间
        参数：
            :param msg: 文字内容
        """
        return self.font.getsize(msg)

    async def apoint(
        self, pos: Tuple[int, int], fill: Optional[Tuple[int, int, int]] = None
    ):
        """
        说明：
            异步 绘制多个或单独的像素
        参数：
            :param pos: 坐标
            :param fill: 填错颜色
        """
        await self.loop.run_in_executor(None, self.point, pos, fill)

    def point(self, pos: Tuple[int, int], fill: Optional[Tuple[int, int, int]] = None):
        """
        说明：
            绘制多个或单独的像素
        参数：
            :param pos: 坐标
            :param fill: 填错颜色
        """
        self.draw.point(pos, fill=fill)

    async def aellipse(
        self,
        pos: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1,
    ):
        """
        说明：
            异步 绘制圆
        参数：
            :param pos: 坐标范围
            :param fill: 填充颜色
            :param outline: 描线颜色
            :param width: 描线宽度
        """
        await self.loop.run_in_executor(None, self.ellipse, pos, fill, outline, width)

    def ellipse(
        self,
        pos: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1,
    ):
        """
        说明：
            绘制圆
        参数：
            :param pos: 坐标范围
            :param fill: 填充颜色
            :param outline: 描线颜色
            :param width: 描线宽度
        """
        self.draw.ellipse(pos, fill, outline, width)

    async def atext(
        self,
        pos: Tuple[int, int],
        text: str,
        fill: Union[str, Tuple[int, int, int]] = (0, 0, 0),
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            异步 在图片上添加文字
        参数：
            :param pos: 文字位置
            :param text: 文字内容
            :param fill: 文字颜色
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        await self.loop.run_in_executor(None, self.text, pos, text, fill, center_type)

    def text(
        self,
        pos: Tuple[int, int],
        text: str,
        fill: Union[str, Tuple[int, int, int]] = (0, 0, 0),
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            在图片上添加文字
        参数：
            :param pos: 文字位置
            :param text: 文字内容
            :param fill: 文字颜色
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        if center_type:
            if center_type not in ["center", "by_height", "by_width"]:
                raise ValueError(
                    "center_type must be 'center', 'by_width' or 'by_height'"
                )
            w, h = self.w, self.h
            ttf_w, ttf_h = self.getsize(text)
            if center_type == "center":
                w = int((w - ttf_w) / 2)
                h = int((h - ttf_h) / 2)
            elif center_type == "by_width":
                w = int((w - ttf_w) / 2)
                h = pos[1]
            elif center_type == "by_height":
                h = int((h - ttf_h) / 2)
                w = pos[0]
            pos = (w, h)
        self.markImg = TextUtil.render_text(
            text=text, image=self, pos=pos, fill=fill
        ).markImg

    async def asave(self, path: Optional[Union[str, Path]] = None):
        """
        说明：
            异步 保存图片
        参数：
            :param path: 图片路径
        """
        await self.loop.run_in_executor(None, self.save, path)

    def save(self, path: Optional[Union[str, Path]] = None):
        """
        说明：
            保存图片
        参数：
            :param path: 图片路径
        """
        if not path:
            path = self.background
        self.markImg.save(path)

    def show(self):
        """
        说明：
            显示图片
        """
        self.markImg.show()

    async def aresize(self, ratio: float = 0, w: int = 0, h: int = 0):
        """
        说明：
            异步 压缩图片
        参数：
            :param ratio: 压缩倍率
            :param w: 压缩图片宽度至 w
            :param h: 压缩图片高度至 h
        """
        await self.loop.run_in_executor(None, self.resize, ratio, w, h)

    def resize(self, ratio: float = 0, w: int = 0, h: int = 0):
        """
        说明：
            压缩图片
        参数：
            :param ratio: 压缩倍率
            :param w: 压缩图片宽度至 w
            :param h: 压缩图片高度至 h
        """
        if not w and not h:
            if not ratio:
                raise AttributeError("缺少参数...")
            w = int(self.w * ratio)
            h = int(self.h * ratio)
        self.markImg = self.markImg.resize((w, h), Resampling.LANCZOS)
        self.w, self.h = self.markImg.size
        self.size = self.w, self.h
        self.draw = ImageDraw.Draw(self.markImg)

    async def acrop(self, box: Tuple[int, int, int, int]):
        """
        说明：
            异步 裁剪图片
        参数：
            :param box: 左上角坐标，右下角坐标 (left, upper, right, lower)
        """
        await self.loop.run_in_executor(None, self.crop, box)

    def crop(self, box: Tuple[int, int, int, int]):
        """
        说明：
            裁剪图片
        参数：
            :param box: 左上角坐标，右下角坐标 (left, upper, right, lower)
        """
        self.markImg = self.markImg.crop(box)
        self.w, self.h = self.markImg.size
        self.size = self.w, self.h
        self.draw = ImageDraw.Draw(self.markImg)

    def check_font_size(self, word: str) -> bool:
        """
        说明：
            检查文本所需宽度是否大于图片宽度
        参数：
            :param word: 文本内容
        """
        return self.font.getsize(word)[0] > self.w

    async def atransparent(self, alpha_ratio: float = 1, n: int = 0):
        """
        说明：
            异步 图片透明化
        参数：
            :param alpha_ratio: 透明化程度
            :param n: 透明化大小内边距
        """
        await self.loop.run_in_executor(None, self.transparent, alpha_ratio, n)

    def transparent(self, alpha_ratio: float = 1, n: int = 0):
        """
        说明：
            图片透明化
        参数：
            :param alpha_ratio: 透明化程度
            :param n: 透明化大小内边距
        """
        self.markImg = self.markImg.convert("RGBA")
        x, y = self.markImg.size
        for i in range(n, x - n):
            for k in range(n, y - n):
                color = self.markImg.getpixel((i, k))
                color = color[:-1] + (int(100 * alpha_ratio),)
                self.markImg.putpixel((i, k), color)
        self.draw = ImageDraw.Draw(self.markImg)

    def pic2bs4(self) -> str:
        """
        说明：
            BuildImage 转 base64
        """
        buf = BytesIO()
        self.markImg.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def pic2bytes(self) -> bytes:
        """
        说明：
            BuildImage 转 base64
        """
        buf = BytesIO()
        self.markImg.save(buf, format="PNG")
        return buf.getvalue()

    def convert(self, type_: str):
        """
        说明：
            修改图片类型
        参数：
            :param type_: 类型
        """
        self.markImg = self.markImg.convert(type_)

    async def arectangle(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: str = None,
        width: int = 1,
    ):
        """
        说明：
            异步 画框
        参数：
            :param xy: 坐标
            :param fill: 填充颜色
            :param outline: 轮廓颜色
            :param width: 线宽
        """
        await self.loop.run_in_executor(None, self.rectangle, xy, fill, outline, width)

    def rectangle(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: str = None,
        width: int = 1,
    ):
        """
        说明：
            画框
        参数：
            :param xy: 坐标
            :param fill: 填充颜色
            :param outline: 轮廓颜色
            :param width: 线宽
        """
        self.draw.rectangle(xy, fill, outline, width)

    async def apolygon(
        self,
        xy: List[Tuple[int, int]],
        fill: Tuple[int, int, int] = (0, 0, 0),
        outline: int = 1,
    ):
        """
        说明:
            异步 画多边形
        参数：
            :param xy: 坐标
            :param fill: 颜色
            :param outline: 线宽
        """
        await self.loop.run_in_executor(None, self.polygon, xy, fill, outline)

    def polygon(
        self,
        xy: List[Tuple[int, int]],
        fill: Tuple[int, int, int] = (0, 0, 0),
        outline: int = 1,
    ):
        """
        说明:
            画多边形
        参数：
            :param xy: 坐标
            :param fill: 颜色
            :param outline: 线宽
        """
        self.draw.polygon(xy, fill, outline)

    async def aline(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Union[str, Tuple[int, int, int]]] = None,
        width: int = 1,
    ):
        """
        说明：
            异步 画线
        参数：
            :param xy: 坐标
            :param fill: 填充
            :param width: 线宽
        """
        await self.loop.run_in_executor(None, self.line, xy, fill, width)

    def line(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Union[Tuple[int, int, int], str]] = None,
        width: int = 1,
    ):
        """
        说明：
            画线
        参数：
            :param xy: 坐标
            :param fill: 填充
            :param width: 线宽
        """
        self.draw.line(xy, fill, width)

    async def acircle(self):
        """
        说明：
            异步 将 BuildImage 图片变为圆形
        """
        await self.loop.run_in_executor(None, self.circle)

    def circle(self):
        """
        说明：
            将 BuildImage 图片变为圆形
        """
        self.convert("RGBA")
        r2 = min(self.w, self.h)
        if self.w != self.h:
            self.resize(w=r2, h=r2)
        r3 = int(r2 / 2)
        imb = Image.new("RGBA", (r3 * 2, r3 * 2), (255, 255, 255, 0))
        pim_a = self.markImg.load()  # 像素的访问对象
        pim_b = imb.load()
        r = float(r2 / 2)
        for i in range(r2):
            lx = abs(i - r)  # 到圆心距离的横坐标
            for j in range(r2):
                ly = abs(j - r)  # 到圆心距离的纵坐标
                l_ = (pow(lx, 2) + pow(ly, 2)) ** 0.5  # 三角函数 半径
                if l_ < r3:
                    pim_b[i - (r - r3), j - (r - r3)] = pim_a[i, j]
        self.markImg = imb

    async def acircle_corner(self, radii: int = 30):
        """
        说明：
            异步 矩形四角变圆
        参数：
            :param radii: 半径
        """
        await self.loop.run_in_executor(None, self.circle_corner, radii)

    def circle_corner(self, radii: int = 30):
        """
        说明：
            矩形四角变圆
        参数：
            :param radii: 半径
        """
        # 画圆（用于分离4个角）
        circle = Image.new("L", (radii * 2, radii * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)
        self.markImg = self.markImg.convert("RGBA")
        w, h = self.markImg.size
        alpha = Image.new("L", self.markImg.size, 255)
        alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))
        alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))
        alpha.paste(
            circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii)
        )
        alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))
        self.markImg.putalpha(alpha)

    async def arotate(self, angle: int, expand: bool = False):
        """
        说明：
            异步 旋转图片
        参数：
            :param angle: 角度
            :param expand: 放大图片适应角度
        """
        await self.loop.run_in_executor(None, self.rotate, angle, expand)

    def rotate(self, angle: int, expand: bool = False):
        """
        说明：
            旋转图片
        参数：
            :param angle: 角度
            :param expand: 放大图片适应角度
        """
        self.markImg = self.markImg.rotate(angle, expand=expand)

    async def atranspose(self, angle: int):
        """
        说明：
            异步 旋转图片(包括边框)
        参数：
            :param angle: 角度
        """
        await self.loop.run_in_executor(None, self.transpose, angle)

    def transpose(self, angle: Literal[0, 1, 2, 3, 4, 5, 6]):
        """
        说明：
            旋转图片(包括边框)
        参数：
            :param angle: 角度
        """
        self.markImg.transpose(angle)

    async def afilter(self, filter_: str, aud: int = None):
        """
        说明：
            异步 图片变化
        参数：
            :param filter_: 变化效果
            :param aud: 利率
        """
        await self.loop.run_in_executor(None, self.filter, filter_, aud)

    def filter(self, filter_: str, aud: int = None):
        """
        说明：
            图片变化
        参数：
            :param filter_: 变化效果
            :param aud: 利率
        """
        _x = None
        if filter_ == "BLUR":
            _x = ImageFilter.BLUR
        elif filter_ == "CONTOUR":
            _x = ImageFilter.CONTOUR
        elif filter_ == "EDGE_ENHANCE":
            _x = ImageFilter.EDGE_ENHANCE
        elif filter_ == "FIND_EDGES":
            _x = ImageFilter.FIND_EDGES
        elif filter_ == "GaussianBlur":
            _x = ImageFilter.GaussianBlur
        if _x:
            self.markImg = (
                self.markImg.filter(_x(aud)) if aud else self.markImg.filter(_x)
            )
        self.draw = ImageDraw.Draw(self.markImg)

    async def areplace_color_tran(
        self,
        src_color: Union[
            Tuple[int, int, int], Tuple[Tuple[int, int, int], Tuple[int, int, int]]
        ],
        replace_color: Tuple[int, int, int],
    ):
        """
        说明：
            异步 颜色替换
        参数：
            :param src_color: 目标颜色，或者使用列表，设置阈值
            :param replace_color: 替换颜色
        """
        self.loop.run_in_executor(
            None, self.replace_color_tran, src_color, replace_color
        )

    def replace_color_tran(
        self,
        src_color: Union[
            Tuple[int, int, int], Tuple[Tuple[int, int, int], Tuple[int, int, int]]
        ],
        replace_color: Tuple[int, int, int],
    ):
        """
        说明：
            颜色替换
        参数：
            :param src_color: 目标颜色，或者使用元祖，设置阈值
            :param replace_color: 替换颜色
        """
        if isinstance(src_color, tuple):
            start_ = src_color[0]
            end_ = src_color[1]
        else:
            start_ = src_color
            end_ = None
        for i in range(self.w):
            for j in range(self.h):
                r, g, b = self.markImg.getpixel((i, j))
                if end_:
                    if (
                        start_[0] <= r <= end_[0]
                        and start_[1] <= g <= end_[1]
                        and start_[2] <= b <= end_[2]
                    ):
                        self.markImg.putpixel((i, j), replace_color)

                elif r == start_[0] and g == start_[1] and b == start_[2]:
                    self.markImg.putpixel((i, j), replace_color)

    async def aget_channel(self, channel):
        """
        说明：
            异步 获取通道
        参数：
            :param channel: 通道
        """
        await self.loop.run_in_executor(None, self.get_channel, channel)

    def get_channel(self, channel):
        self.markImg = self.markImg.getchannel(channel)

    async def adraw_ellipse(self, bounds, width=1, outline="white", antialias=4):
        """
        说明：
            异步 绘制椭圆
        参数：
            :param bounds: 椭圆范围
            :param width: 线宽
            :param outline: 线条颜色
            :param antialias: 抗锯齿
        """
        await self.loop.run_in_executor(
            None, self.draw_ellipse, bounds, width, outline, antialias
        )

    def draw_ellipse(self, bounds, width=1, outline="white", antialias=4):
        mask = Image.new(
            size=[int(dim * antialias) for dim in self.markImg.size],
            mode="L",
            color="black",
        )
        draw = ImageDraw.Draw(mask)
        for offset, fill in (width / -2.0, "black"), (width / 2.0, outline):
            left, top = [(value + offset) * antialias for value in bounds[:2]]
            right, bottom = [(value - offset) * antialias for value in bounds[2:]]
            draw.ellipse([left, top, right, bottom], fill=fill)
        mask = mask.resize(self.markImg.size, Image.LANCZOS)
        self.markImg.putalpha(mask)

    async def acircle_new(self):
        """
        说明：
            异步 画圆
        """
        await self.loop.run_in_executor(None, self.circle_new)

    def circle_new(self):
        self.markImg.convert("RGBA")
        size = self.markImg.size
        r2 = min(size[0], size[1])
        if size[0] != size[1]:
            self.markImg = self.markImg.resize((r2, r2), Resampling.LANCZOS)
        ellipse_box = [0, 0, r2 - 2, r2 - 2]
        self.draw_ellipse(ellipse_box, width=1)

    def get_font_variation_names(self):
        """
        说明：
            获取字体变体名称
        :return: 字体变体名称列表
        """
        return self.font.get_variation_names()

    def set_font_variation_by_name(self, variation: str):
        """
        说明：
            设置字体变体
        :param variation: 字体变体名称
        """
        self.font.set_variation_by_name(variation)


class TextUtil:
    @staticmethod
    def get_emoji_loc(text: str) -> List[Tuple[str, int]]:
        loc = []
        for emoji in emoji_list:
            emoji_index = [index for index, char in enumerate(text) if char == emoji]
            loc.extend((emoji, index) for index in emoji_index)
        return loc

    @staticmethod
    def replace_emoji(text: str, __new: str = "\u3000") -> str:
        for emoji in emoji_list:
            text = text.replace(emoji, __new)
        return text

    @staticmethod
    def render_text(
        text: str,
        image: BuildImage,
        pos: Tuple[int, int],
        max_length: int = 0,
        fill: Union[str, Tuple[int, int, int]] = (0, 0, 0),
    ) -> BuildImage:
        max_length = max_length or image.w - pos[0]
        emoji_loc = groupby(
            TextUtil.get_emoji_loc(
                text=TextUtil.auto_newline(
                    text=text,
                    font=image.font,
                    max_length=max_length,
                )
            ),
            key=lambda x: x[0],
        )
        emoji_loc = list(map(lambda x: [x[0], list(x[1])], emoji_loc))
        image.draw.text(
            xy=pos,
            text=TextUtil.auto_newline(
                text=TextUtil.replace_emoji(text),
                font=image.font,
                max_length=max_length,
            ),
            fill=fill,
            font=image.font,
        )
        emoji_size_x, emoji_size_y = map(
            lambda x: (math.ceil(x * 0.8)),
            image.font.getsize("\u3000"),
        )
        for emoji, loc in emoji_loc:
            file = Path(
                Path(__file__).parent, "assets", "emoji", "image", f"{ord(emoji)}.png"
            )
            if file.is_file():
                emoji_image = (
                    Image.open(file)
                    .convert("RGBA")
                    .resize(
                        (emoji_size_x, emoji_size_y),
                        Resampling.LANCZOS,
                    )
                )
                for index in loc:
                    pos_x, pos_y = TextUtil.get_index_loc(
                        index=index[1],
                        text=TextUtil.auto_newline(
                            text=TextUtil.replace_emoji(text),
                            font=image.font,
                            max_length=max_length,
                        ),
                        font=image.font,
                    )
                    pos_x = (
                        pos_x
                        + pos[0]
                        + math.ceil(
                            (min(image.font.getsize("\u3000")) - emoji_size_x) * 0.5
                        )
                    )
                    pos_y = (
                        pos_y
                        + pos[1]
                        + math.ceil(
                            (min(image.font.getsize("\u3000")) - emoji_size_y) * 0.5
                        )
                    )
                    image.paste(
                        emoji_image,
                        (pos_x, pos_y),
                        alpha=True,
                    )
        return image

    @staticmethod
    def auto_newline(text: str, font: FreeTypeFont, max_length: int) -> str:
        if max_length <= 0:
            raise ValueError("max_length equals to or less than 0")
        lines = []
        for line in text.splitlines():
            line_text = ""
            for char_index, char in enumerate(line):
                if font.getsize(line_text + char)[0] > max_length:
                    lines.append(line_text)
                    line_text = char
                    if char_index == len(line) - 1:
                        lines.append(line_text)
                    continue
                line_text = line_text + char
                if char_index == len(line) - 1:
                    lines.append(line_text)
        return "\n".join(lines)

    @staticmethod
    def get_index_loc(index: int, text: str, font: FreeTypeFont) -> Tuple[int, int]:
        if index > len(text) - 1:
            raise IndexError("index greater than text length")
        if not text or not text[:index].splitlines():
            return 0, 0
        prev_lines = text[:index].splitlines()[:-1]
        last_line = text[:index].splitlines()[-1]
        return font.getsize(last_line)[0] if text[index - 1] != "\n" else 0, sum(
            [font.getsize("\n".join(line))[1] for line in prev_lines]
            + [font.getsize(last_line)[1] if text[index - 1] == "\n" else 0]
        )

    @staticmethod
    def text_to_one_line(text: str, font: FreeTypeFont, max_length: int) -> str:
        if font.getsize(text)[0] <= max_length:
            return text
        new_text = ""
        for char in text:
            if font.getsize(new_text + char + "...")[0] > max_length:
                return f"{new_text}..."
            new_text = new_text + char

    @classmethod
    def get_line_count(cls, text: str, font: FreeTypeFont, max_length: int) -> int:
        return len(
            cls.auto_newline(cls.replace_emoji(text), font, max_length).splitlines()
        )

    @classmethod
    def get_text_box(
        cls, text: str, font: FreeTypeFont, max_length: int
    ) -> Tuple[int, int]:
        return max(
            font.getsize(line)[0]
            for line in cls.auto_newline(
                cls.replace_emoji(text), font, max_length
            ).splitlines()
        ), sum(
            font.getsize(line)[1]
            for line in cls.auto_newline(
                cls.replace_emoji(text), font, max_length
            ).splitlines()
        )
