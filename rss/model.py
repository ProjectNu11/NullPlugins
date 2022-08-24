from datetime import datetime
from time import mktime
from typing import Iterator

from graia.broadcast import Dispatchable, BaseDispatcher
from graia.saya import Channel
from pydantic import BaseModel, Field, validator

channel = Channel.current()


class RSSFeedItem(BaseModel):
    title: str
    """ Title """

    summary: str
    """ Summary """

    published: datetime = Field(alias="published_parsed")
    """ Published time """

    id: str
    """ ID """

    link: str
    """ Guid"""

    author: str
    """ Author """

    @validator("published", pre=True)
    def parse_published(cls, v):
        return mktime(v)


class RSSFeedItems(BaseModel):
    items: list[RSSFeedItem]

    def __init__(self, *items: RSSFeedItem):
        items = list(items)
        super().__init__(items=items)
        self.items = items

    def __iter__(self) -> Iterator[RSSFeedItem]:
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __bool__(self):
        return bool(self.items)


class RSSFeed(BaseModel):
    """
    RSS Feed
    """

    title: str
    url: str
    groups: set[int] = set()
    friends: set[int] = set()
    last_id: str = ""
    last_update: datetime = datetime.fromtimestamp(0)

    def update(self, items: RSSFeedItems):
        latest = max(items.items, key=lambda x: x.published)
        self.last_id = latest.id
        self.last_update = latest.published


class RSSUpdate(Dispatchable):
    feed: RSSFeed
    items: RSSFeedItems

    def __init__(self, feed: RSSFeed, items: RSSFeedItems):
        self.feed = feed
        self.items = items

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: "DispatcherInterface['RSSUpdate']"):
            if interface.annotation is interface.event.feed.__class__:
                return interface.event.feed
            if interface.annotation is interface.event.items.__class__:
                return interface.event.items
            if interface.name == "feed":
                return interface.event.feed
            if interface.name == "items":
                return interface.event.items
