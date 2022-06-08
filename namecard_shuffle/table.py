from sqlalchemy import Column, DateTime, BIGINT, String

from library.orm import Base


class NameCardBackup(Base):
    """群名片备份"""

    __tablename__ = "name_card_backup"

    time = Column(DateTime, nullable=False, primary_key=True)
    group = Column(BIGINT, nullable=False, primary_key=True)
    member = Column(BIGINT, nullable=False, primary_key=True)
    before = Column(String(length=4000), nullable=False)
    after = Column(String(length=4000), nullable=False)
