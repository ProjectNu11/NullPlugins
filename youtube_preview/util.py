from graia.ariadne import Ariadne
from graia.saya import Channel

from library import config
from library.image.oneui_mock.elements import (
    Column,
    Banner,
    GeneralBox,
    HintBox,
    OneUIMock,
)
from .model import Response
from .var import ENDPOINT, SHORT_LINK_PATTERN, VIDEO_LINK_PATTERN

channel = Channel.current()


async def query(
    ids: list[int | str], *, banner_text: str = "YouTube 预览"
) -> Response | bytes:
    try:
        assert (
            key := config.get_module_config(channel.module, "key")
        ), "YouTube API Key 未配置"
        ids = list(map(lambda x: str(x), ids))
        _ids: str = ",".join(ids)
        async with Ariadne.service.client_session.get(
            ENDPOINT.format(ids=_ids, key=key), proxy=config.proxy
        ) as resp:
            assert resp.status == 200, f"HTTP {resp.status}"
            data = await resp.json()
            response = Response(**data)
            assert response.items, "未找到视频"
            return response
    except AssertionError as err:
        return await compose_error(err.args[0], banner_text)
    except Exception as err:
        return await compose_error(str(err), banner_text)


async def compose_error(err_text: str, banner_text: str) -> bytes:
    column = Column()
    banner = Banner(banner_text)
    column.add(banner)
    box = GeneralBox(
        text="运行搜索时出现错误",
        description=err_text,
    )
    column.add(box)
    hint = HintBox(
        "可以尝试以下解决方案",
        "检查网络连接是否正常",
        "检查是否超过查询速率限制",
        "检查用户或 API 密钥是否有效",
    )
    column.add(hint)
    mock = OneUIMock(column)
    return await mock.async_render_bytes()


async def get_status_link(short_link: str) -> str | None:
    if not short_link.startswith("http"):
        short_link = f"https://{short_link}"
    async with Ariadne.service.client_session.get(
        url=short_link, proxy=config.proxy, verify_ssl=False
    ) as res:
        if VIDEO_LINK_PATTERN.findall(str(res.url)):
            return str(res.url)


async def get_video_id(message: str) -> list[str]:
    status_links = []
    if short_links := SHORT_LINK_PATTERN.findall(message):
        for short_link in short_links:
            if link := await get_status_link(short_link):
                status_links.append(link)
    if status_ids := VIDEO_LINK_PATTERN.findall(message + " ".join(status_links)):
        return status_ids
    return []
