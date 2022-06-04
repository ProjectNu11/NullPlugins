from sqlalchemy import Column, String, DateTime, BIGINT

from library.orm import Base


class ImageModeration(Base):
    """图片审核"""

    __tablename__ = "image_moderation"

    id = Column(String(length=200), primary_key=True)
    time = Column(DateTime, nullable=False)
    label = Column(String(length=200), nullable=False)
    suggestion = Column(String(length=200), nullable=False)
    sub_label = Column(String(length=200), nullable=False)
    override = Column(BIGINT, nullable=False)


class ViolationCount(Base):
    """违规计数"""

    __tablename__ = "violation_count"

    group_id = Column(BIGINT, nullable=False, primary_key=True)
    member_id = Column(BIGINT, nullable=False, primary_key=True)
    count = Column(BIGINT, nullable=False)
