import asyncio
import json
from contextvars import ContextVar
from pathlib import Path

from graia.ariadne import Ariadne
from graia.saya import Channel
from loguru import logger
from sqlalchemy import select

from library import config
from library.image.oneui_mock.elements import (
    Banner,
    Column,
    GeneralBox,
    HintBox,
    OneUIMock,
)
from library.orm import orm
from module.snowball_news.model import NewsItem
from module.snowball_news.table import SnowballNews

channel = Channel.current()

HOMEPAGE_URL = "http://xueqiu.com"
HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Host": "xueqiu.com",
    "Referer": "http://xueqiu.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/67.0.3396.99 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}
LIVENEWS_URL = "https://xueqiu.com/statuses/livenews/list.json?since_id={since_id}"

INTERVAL = 10
QUERY_INTERVAL = 1

cookie = None

sent_id = 0

registered = ContextVar("snowball_registered_groups")
registered.set({"friend": [], "group": []})


async def get_cookie():
    async with Ariadne.service.client_session.get(
        HOMEPAGE_URL, headers=HEADERS, cookies=None, proxy=config.proxy, timeout=10
    ) as response:
        global cookie
        cookie = response.cookies


def parse_result(result: dict) -> list[NewsItem]:
    assert "items" in result, "Cookie 无效"
    items = result["items"]
    result = [NewsItem(**item) for item in items]
    return result


async def query(since_id: int = -1, retries: int = 0) -> list[NewsItem]:
    try:
        if retries > 3:
            return []
        async with Ariadne.service.client_session.get(
            LIVENEWS_URL.format(since_id=since_id),
            headers=HEADERS,
            cookies=cookie,
            proxy=config.proxy,
            timeout=10,
        ) as response:
            result = await response.json()
            return parse_result(result)
    except AssertionError as err:
        logger.error(err.args[0])
        await get_cookie()
        logger.info(f"重试第 {retries + 1} 次")
        return await query(since_id, retries + 1)
    except asyncio.exceptions.TimeoutError as err:
        logger.error(str(err))
        logger.info(f"重试第 {retries + 1} 次")
        return await query(since_id, retries + 1)


async def insert_news(news: list[NewsItem]):
    for item in news:
        await orm.insert_or_update(
            SnowballNews, [SnowballNews.id == item.id], item.dict()
        )


async def run_once():
    if news := await query():
        await insert_news(news)


async def fetch_from_db(news_id: int) -> NewsItem:
    if result := await orm.all(
        select(
            SnowballNews.id,
            SnowballNews.title,
            SnowballNews.text,
            SnowballNews.target,
            SnowballNews.created_at,
        ).where(SnowballNews.id == news_id)
    ):
        result = result[0]
        return NewsItem(**result)


async def bulk_fetch_from_db(
    since_id: int = None, count: int = None, set_sent: bool = False
) -> list[NewsItem]:
    global sent_id
    if not (
        result := await orm.all(
            select(
                SnowballNews.id,
                SnowballNews.title,
                SnowballNews.text,
                SnowballNews.target,
                SnowballNews.created_at,
            ).order_by(SnowballNews.id.desc())
        )
    ):
        return []
    result.sort(key=lambda x: x[0], reverse=True)
    if not sent_id and not since_id:
        count = 10 if count is None else count
    if not since_id:
        since_id = sent_id
    if set_sent:
        sent_id = result[0][0]
    if count:
        return [NewsItem(**item) for item in result[:count]]
    return [NewsItem(**item) for item in result if item[0] > since_id]


async def compose(*news: NewsItem) -> bytes:
    assert news

    column = Column(Banner("雪球实时新闻"))

    for item in news:
        box = GeneralBox()
        box.add(text="标题", description=item.title, highlight=True)
        box.add(text="摘要", description=item.text)
        box.add(text="时间", description=item.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        box.add(text="编号", description=str(item.id))
        column.add(box)

    cfg = GeneralBox(text="当前发送间隔", description=f"{INTERVAL} 分钟", highlight=True)
    cfg.add(text="当前查询间隔", description="1 分钟", highlight=True)

    column.add(
        HintBox(
            "可用功能",
            f"{config.func.prefix[0]}实时新闻 开启\n    -> 开启实时新闻推送",
            f"{config.func.prefix[0]}实时新闻 关闭\n    -> 关闭实时新闻推送",
            f"{config.func.prefix[0]}实时新闻 查看 [编号]\n    -> 查看特定[编号]的新闻",
            f"{config.func.prefix[0]}实时新闻 查看 [数字]条\n    -> 查看最新的[数字]条新闻",
        ),
        cfg,
    )

    mock = OneUIMock(column)

    return await mock.async_render_bytes()


async def compose_general(text: str, description: str) -> bytes:
    column = Column(Banner("雪球实时新闻"))

    box = GeneralBox(text=text, description=description)

    cfg = GeneralBox(text="当前发送间隔", description=f"{INTERVAL} 分钟", highlight=True)
    cfg.add(text="当前查询间隔", description=f"{QUERY_INTERVAL} 分钟", highlight=True)

    column.add(box, cfg)
    mock = OneUIMock(column)
    return await mock.async_render_bytes()


DATA_PATH = Path(config.path.data, channel.module)
DATA_PATH.mkdir(exist_ok=True)

REG_PATH = Path(config.path.data, channel.module, "reg.json")

if REG_PATH.is_file():
    with REG_PATH.open("r", encoding="utf-8") as _:
        registered.set(json.load(_))
else:
    with REG_PATH.open("w", encoding="utf-8") as _:
        json.dump(registered.get(), _)


def register(friend: int = None, group: int = None):
    data = registered.get()
    if friend:
        assert friend not in data["friend"], "已为你开启实时新闻"
        data["friend"].append(friend)
        return
    if group:
        assert group not in data["group"], "已在本群开启实时新闻"
        data["group"].append(group)
    registered.set(data)
    with REG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f)


def unregister(friend: int = None, group: int = None):
    data = registered.get()
    if friend:
        assert friend in data["friend"], "未为你开启实时新闻"
        data["friend"].remove(friend)
        return
    if group:
        assert group in data["group"], "未在本群开启实时新闻"
        data["group"].remove(group)
    registered.set(data)
    with REG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f)


async def compose_error(err_text: str) -> bytes:
    column = Column(Banner("雪球实时新闻"))
    box = GeneralBox(text="运行时出现错误", description=err_text)
    column.add(box)
    hint = HintBox(
        "可以尝试以下解决方案",
        "检查是否重复设置开关",
        "检查编号是否存在",
        "检查网络连接是否正常",
        "检查是否超过查询速率限制",
        "检查用户或 API 是否有效",
    )
    column.add(hint)
    mock = OneUIMock(column)
    return await mock.async_render_bytes()
