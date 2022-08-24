from sqlalchemy import Column, Integer, DateTime, String, TEXT

from library.orm import Base


class RSSFeedTable(Base):
    """RSS Feed"""

    __tablename__ = "rss_feed"

    feed_id = Column(Integer, primary_key=True)
    title = Column(TEXT(length=4000), nullable=False)
    summary = Column(TEXT(length=4000), nullable=False)
    published = Column(DateTime, nullable=False)
    id = Column(TEXT(length=4000), nullable=False)
    link = Column(TEXT(length=4000), nullable=False)
    author = Column(TEXT(length=4000), nullable=False)
    feed = Column(TEXT(length=4000), nullable=False)
