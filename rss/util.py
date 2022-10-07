import contextlib

import feedparser
from graia.ariadne import Ariadne
from sqlalchemy import select

from library import config
from library.orm import orm
from .model import RSSFeed, RSSFeedItems, RSSFeedItem
from .table import RSSFeedTable

SLEEP_SECONDS = 5
QUERY_INTERVAL_MINUTES = 1


async def get_feed(
    feed: RSSFeed, update: bool = True, suppress: bool = False
) -> RSSFeedItems:
    items: list[RSSFeedItem] = []
    with contextlib.suppress(Exception if suppress else None):
        async with Ariadne.service.client_session.get(
            feed.url, proxy=config.proxy, timeout=10
        ) as response:
            assert response.status == 200, f"HTTP {response.status}"
            result = await response.text()
            feeds = feedparser.parse(result)
            items.extend(RSSFeedItem(**entry) for entry in feeds["entries"])
        items.sort(key=lambda x: x.published, reverse=True)
        _feeds = RSSFeedItems(*items)
        if update:
            feed.update(_feeds)
        _feeds = await filter_new_update(feed, _feeds)
        await insert_db(feed, _feeds)
        return _feeds


async def insert_db(feed: RSSFeed, items: RSSFeedItems):
    for item in sorted(items, key=lambda x: x.published, reverse=False):
        await orm.add(
            RSSFeedTable,
            {
                "title": item.title,
                "summary": item.summary,
                "published": item.published,
                "id": item.id,
                "link": item.link,
                "author": item.author,
                "feed": feed.title,
            },
        )


async def fetch_last_id(feed: RSSFeed) -> str | None:
    if result := await orm.first(
        select(RSSFeedTable.id)
        .where(RSSFeedTable.feed == feed.title)
        .order_by(RSSFeedTable.feed_id.desc())
        .limit(1)
    ):
        return result[0]


async def filter_new_update(feed: RSSFeed, items: RSSFeedItems) -> RSSFeedItems:
    if last_id := await fetch_last_id(feed):
        new_items = []
        for item in items:
            if item.id == last_id:
                break
            new_items.append(item)
        items = RSSFeedItems(*new_items)
    return items
