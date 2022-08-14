from datetime import datetime

from pydantic import BaseModel


class DBUser(BaseModel):
    id: str
    name: str
    register_time: datetime
    banned: bool
    view_count: int = 0
    reply_count: int = 0
    delete_count: int = 0
    kept_bottle: str = ""


class DBottle(BaseModel):
    id: str
    time: datetime
    sender: str
    content: str
    status: int
    view_times: int


class DBReply(BaseModel):
    id: str
    bottle_id: str
    time: datetime
    sender: str
    content: str
