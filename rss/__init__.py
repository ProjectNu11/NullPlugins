import asyncio

from graia.ariadne import Ariadne
from graia.saya import Channel
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

from .decorator import FeedFilter
from .feeds import feeds
from .model import RSSFeed, RSSUpdate, RSSFeedItems, RSSFeedItem
from .util import (
    get_feed,
    insert_db,
    fetch_last_id,
    filter_new_update,
    QUERY_INTERVAL_MINUTES,
    SLEEP_SECONDS,
)

channel = Channel.current()


@channel.use(SchedulerSchema(timer=timers.every_custom_minutes(QUERY_INTERVAL_MINUTES)))
async def get_rss_update(app: Ariadne):
    for _feed in feeds:
        if feed_update := await get_feed(_feed):
            app.broadcast.postEvent(RSSUpdate(feed=_feed, items=feed_update))
        await asyncio.sleep(SLEEP_SECONDS)
