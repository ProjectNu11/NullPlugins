from sqlalchemy import Column, Integer, DateTime, String, TEXT

from library.orm import Base


class RSSFeedTable(Base):
    """RSS Feed"""

    __tablename__ = "rss_feed"

    feed_id = Column(Integer, primary_key=True)
    title = Column(TEXT, nullable=False)
    summary = Column(TEXT, nullable=False)
    published = Column(DateTime, nullable=False)
    id = Column(TEXT, nullable=False)
    link = Column(TEXT, nullable=False)
    author = Column(TEXT, nullable=False)
    feed = Column(TEXT, nullable=False)
