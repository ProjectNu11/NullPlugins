from sqlalchemy import Column, Integer, DateTime, String

from library.orm import Base


class RSSFeedTable(Base):
    """RSS Feed"""

    __tablename__ = "rss_feed"

    feed_id = Column(Integer, primary_key=True)
    title = Column(String(length=4000), nullable=False)
    summary = Column(String(length=4000), nullable=False)
    published = Column(DateTime, nullable=False)
    id = Column(String(length=4000), nullable=False)
    link = Column(String(length=4000), nullable=False)
    author = Column(String(length=4000), nullable=False)
    feed = Column(String(length=4000), nullable=False)
