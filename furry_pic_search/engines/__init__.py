from library.image.oneui_mock.elements import (
    Banner,
    Column,
    is_dark,
    GeneralBox,
    HintBox,
    OneUIMock,
)
from .base import BaseSearch
from .e621 import E621Search, E621_CFG_KEYS

__all__: dict[str, BaseSearch] = {
    "e621": E621Search(),
}

__cfg__: dict[str, list[str]] = {"e621": E621_CFG_KEYS}


async def run_search(
    engine: BaseSearch, *tags: str, get_random: bool, rating: str = None
) -> bytes:
    try:
        return await engine.get(*tags, get_random=get_random, rating=rating)
    except AssertionError as err:
        err_text = err.args[0]
    except Exception as err:
        err_text = str(err)
    return await compose_error(engine, err_text)


async def compose_error(engine: BaseSearch, err_text: str) -> bytes:
    dark = is_dark()
    column = Column(dark=dark)
    banner = Banner(f"{engine.__name__} 图片搜索", dark=dark)
    column.add(banner)
    box = GeneralBox(text="运行搜索时出现错误", description=err_text, dark=dark)
    column.add(box)
    hint = HintBox(
        "可以尝试以下解决方案",
        "换用其他搜索引擎",
        "换用英文标签",
        "检查标签是否存在",
        "检查网络连接是否正常",
        "检查标签是否在屏蔽词内",
        "检查是否超过查询速率限制",
        "检查用户或 API 密钥是否有效",
        dark=dark,
    )
    column.add(hint)
    mock = OneUIMock(column, dark=dark)
    return await mock.async_render_bytes()
