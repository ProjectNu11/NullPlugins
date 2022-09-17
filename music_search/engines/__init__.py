import asyncio
from pathlib import Path

from PIL import Image
from graia.ariadne.message.element import MusicShare

from library.image.oneui_mock.elements import (
    Banner,
    Column,
    GeneralBox,
    HintBox,
    OneUIMock,
)
from .base import BaseSearch
from .netease import NetEaseSearch

__all__: dict[str, BaseSearch] = {"netease": NetEaseSearch, "网易": NetEaseSearch}


async def run_search(
    engine: BaseSearch, *keywords: str
) -> tuple[Image.Image, list[MusicShare]]:
    try:
        assert keywords, "没有搜索关键词"
        return await engine.search(*keywords)
    except AssertionError as err:
        err_text = err.args[0]
    except Exception as err:
        err_text = str(err)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, compose_error, engine, err_text)


def compose_error(
    engine: BaseSearch, err_text: str
) -> tuple[Image.Image, list[MusicShare]]:
    column = Column()
    banner = Banner(
        f"{engine.engine_name} 歌曲搜索",
        icon=Image.open(Path(__file__).parent.parent / "icon.png"),
    )
    column.add(banner)
    box = GeneralBox(text="运行搜索时出现错误", description=err_text)
    column.add(box)
    hint = HintBox(
        "可以尝试以下解决方案",
        "换用其他搜索引擎",
        "检查歌曲是否存在",
        "检查网络连接是否正常",
        "检查是否超过查询速率限制",
        "检查 API 是否有效",
    )
    column.add(hint)
    mock = OneUIMock(column)
    return mock.render(), []
