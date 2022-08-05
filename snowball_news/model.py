import re
from datetime import datetime

from pydantic import BaseModel, root_validator


class NewsItem(BaseModel):
    id: int
    title: str = "暂无标题"
    text: str
    target: str
    created_at: datetime

    @root_validator()
    def generate_title(cls, values):
        if values.get("title") == "暂无标题":
            if result := re.findall(r"【(.*?)】", values.get("text")):
                values["title"] = result[0]
        return values
