import asyncio
import contextlib

from graia.ariadne import Ariadne
from graia.saya import Channel
from pydantic import ValidationError

from library import config
from library.image.oneui_mock.elements import (
    Column,
    Banner,
    GeneralBox,
    HintBox,
    OneUIMock,
)
from .model.response import Response, ErrorResponse
from .var import ENDPOINT, SHORT_LINK_PATTERN, STATUS_LINK_PATTERN

channel = Channel.current()


async def query(
    ids: list[int | str], *, banner_text: str = "Twitter 预览", exclude_error: bool = True
) -> Response | ErrorResponse | bytes:
    try:
        assert (
            bearer := config.get_module_config(channel.module, "bearer")
        ), "推特 Bearer 未配置"
        headers = {"Authorization": f"Bearer {bearer}"}

        ids = list(map(lambda x: str(x), ids))
        _ids: str = ",".join(ids)
        async with Ariadne.service.client_session.get(
            ENDPOINT.format(ids=_ids), proxy=config.proxy, headers=headers
        ) as resp:
            try:
                data = await resp.json()
                return Response(**data)
            except ValidationError:
                raise
                err_resp = ErrorResponse(**data)
                if not exclude_error:
                    return err_resp
                for _id in err_resp.get_id():
                    _id = str(_id)
                    with contextlib.suppress(ValueError):
                        ids.remove(_id)
                    return await query(
                        ids=ids, banner_text=banner_text, exclude_error=False
                    )
    except AssertionError as err:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, compose_error, err.args[0], banner_text)
    except Exception as err:
        raise
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, compose_error, str(err), banner_text)


def compose_error(err_text: str, banner_text: str) -> bytes:
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
    return mock.render_bytes()


async def get_status_link(short_link: str) -> str | None:
    if not short_link.startswith("http"):
        short_link = f"https://{short_link}"
    async with Ariadne.service.client_session.get(
        url=short_link, proxy=config.proxy, verify_ssl=False
    ) as res:
        if STATUS_LINK_PATTERN.findall(str(res.url)):
            return str(res.url)


async def get_status_id(message: str) -> list[str]:
    status_links = []
    if short_links := SHORT_LINK_PATTERN.findall(message):
        for short_link in short_links:
            if link := await get_status_link(short_link):
                status_links.append(link)
    if status_ids := STATUS_LINK_PATTERN.findall(message + " ".join(status_links)):
        return status_ids
    return []
