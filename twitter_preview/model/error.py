import asyncio
import re

from loguru import logger
from pydantic import BaseModel

from library.image.oneui_mock.elements import (
    Column,
    Banner,
    GeneralBox,
    OneUIMock,
    HintBox,
)


class TweetError(BaseModel):
    resource_id: int
    parameter: str
    resource_type: str
    section: str
    title: str
    value: int
    detail: str
    type: str

    async def compose(self, banner_text: str = "Twitter 预览") -> bytes:
        def __compose() -> bytes:
            column = Column(
                Banner(banner_text),
            )
            box = GeneralBox(
                text="取得推文时出错", description=f"请求以下推文 ID 时出错：{self.resource_id}"
            )
            box.add(text="出错原因", description=self.title)
            box.add(text="出错详情", description=self.detail)
            column.add(box)

            column.add(
                HintBox(
                    "可以尝试以下解决方案",
                    "检查推文发送者是否为私人推特",
                    "检查是否传入正确的推文 ID",
                    "检查参数是否配置正确",
                    "检查是否超过查询速率限制",
                    "检查用户或 API 密钥是否有效",
                )
            )

            return OneUIMock(column).render_bytes()

        logger.info(f"渲染报错 {self.resource_id} 中...")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, __compose)


class GeneralError(BaseModel):
    parameters: dict
    message: str

    def get_id(self) -> int:
        if result := re.findall(r"\[(\d+)]", self.message):
            return int(result[0])

    async def compose(self, banner_text: str = "Twitter 预览") -> bytes:
        tweet_id = self.get_id()

        def __compose() -> bytes:
            column = Column(
                Banner(banner_text),
                GeneralBox(text="取得推文时出错", description=f"请求的推文 ID 无效：{tweet_id}"),
            )

            return OneUIMock(column).render_bytes()

        logger.info(f"渲染报错 {tweet_id} 中...")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, __compose)
