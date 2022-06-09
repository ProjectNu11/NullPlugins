from sqlalchemy import Column, Integer, DateTime, BIGINT, String

from library.orm import Base


class ChatRecord(Base):
    """聊天记录表"""

    __tablename__ = "chat_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    field = Column(String(length=200), nullable=False)
    sender = Column(String(length=200), nullable=False)
    persistent_string = Column(String(length=4000), nullable=False)
    seg = Column(String(length=4000), nullable=False)


class SendRecord(Base):
    """发送记录表"""

    __tablename__ = "send_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    target = Column(BIGINT, nullable=False)
    type = Column(String(length=10), nullable=False)
    persistent_string = Column(String(length=4000), nullable=False)
