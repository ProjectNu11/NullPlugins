from sqlalchemy import Column, Integer, DateTime, BIGINT, String

from library.orm import Base


class WalletBalance(Base):
    """钱包"""

    __tablename__ = "wallet"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT, primary_key=True)
    balance = Column(BIGINT, nullable=False, default=0)
    time = Column(DateTime, nullable=False)


class WalletDetail(Base):
    """钱包明细"""

    __tablename__ = "wallet_detail"

    id = Column(Integer, primary_key=True)
    group_id = Column(BIGINT, nullable=False, default=0)
    member_id = Column(BIGINT, nullable=False, default=0)
    record = Column(BIGINT, nullable=False, default=0)
    reason = Column(String(length=200), nullable=False, default="0")
    balance = Column(BIGINT, nullable=False, default=0)
    time = Column(DateTime, nullable=False)
