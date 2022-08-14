from sqlalchemy import Column, DateTime, BIGINT, String, Boolean

from library.orm import Base


class DriftBottleUser(Base):
    """DriftBottleUser"""

    __tablename__ = "drift_bottle_user"

    id = Column(String(length=32), primary_key=True)
    """User ID, md5 of user id"""

    name = Column(String(length=32), nullable=False)
    """User Name"""

    register_time = Column(DateTime, nullable=False)
    """Register Time"""

    banned = Column(Boolean, nullable=False, default=False)
    """Banned"""

    view_count = Column(BIGINT, nullable=False, default=0)
    """View Count"""

    reply_count = Column(BIGINT, nullable=False, default=0)
    """Reply Count"""

    delete_count = Column(BIGINT, nullable=False, default=0)
    """Delete Count"""

    kept_bottle = Column(String(length=32), nullable=False, default="")
    """Kept Bottle ID"""


class DriftBottle(Base):
    """DriftBottle"""

    __tablename__ = "drift_bottle"

    id = Column(String(length=32), primary_key=True)
    """Drift Bottle ID, unique"""

    time = Column(DateTime, nullable=False)
    """Time"""

    sender = Column(String(length=32), nullable=False)
    """Sender"""

    content = Column(String(length=4000), nullable=False)
    """Content"""

    status = Column(BIGINT, nullable=False, default=0)
    """Status, 0: not read, 1: kept, 2: deleted"""

    view_times = Column(BIGINT, nullable=False, default=0)
    """View Times"""


class DriftBottleReply(Base):
    """DriftBottleReply"""

    __tablename__ = "drift_bottle_reply"

    id = Column(String(length=32), primary_key=True)
    """Drift Bottle Reply ID, unique"""

    bottle_id = Column(String(length=32), nullable=False)
    """Drift Bottle ID"""

    time = Column(DateTime, nullable=False)
    """Time"""

    sender = Column(String(length=32), nullable=False)
    """Sender"""

    content = Column(String(length=4000), nullable=False)
    """Content"""
