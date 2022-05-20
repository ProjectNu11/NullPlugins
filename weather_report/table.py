from sqlalchemy import Column, BIGINT, String

from library.orm import Base


class WeatherSchedule(Base):
    """天气订阅"""

    __tablename__ = "weather_schedule"

    supplicant = Column(BIGINT, primary_key=True)
    time = Column(String(length=4), primary_key=True)
    city = Column(String(length=200), nullable=False)
