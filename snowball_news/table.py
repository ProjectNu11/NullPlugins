from sqlalchemy import Column, Integer, DateTime, String

from library.orm import Base


class SnowballNews(Base):
    """雪球新闻表"""

    __tablename__ = "snowball_news"

    id = Column(Integer, primary_key=True)
    title = Column(String(length=4000), nullable=False)
    text = Column(String(length=4000), nullable=False)
    target = Column(String(length=4000), nullable=False)
    created_at = Column(DateTime, nullable=False)
