from typing import NoReturn, Callable

from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from .model import RSSUpdate, RSSFeed


class FeedFilter:
    @staticmethod
    def check(*feeds: str, criteria: list[Callable[[RSSFeed], bool]] = None) -> Depend:
        """
        Check if the feed title is in the filter list.

        :param feeds: RSS feed
        :param criteria: criteria to check, recommend to use `lambda`
        :return: True if the feed is in the filter list, False otherwise.
        """

        async def feed_filter(event: RSSUpdate) -> NoReturn:
            if event.feed.title.split(":")[0] not in feeds:
                raise ExecutionStop()
            if criteria and all(criterion(event.feed) for criterion in criteria):
                raise ExecutionStop()

        return Depend(feed_filter)
