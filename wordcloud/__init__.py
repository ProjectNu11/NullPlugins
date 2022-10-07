import asyncio
import random
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import aiohttp
import jieba.analyse
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PillowImage
from dateutil.relativedelta import relativedelta
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import (
    GroupMessage,
    FriendMessage,
    MessageEvent,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    RegexMatch,
    MatchResult,
    ElementMatch,
    ElementResult,
    ArgumentMatch,
    ArgResult,
)
from graia.ariadne.model import Member, Friend
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger
from sqlalchemy import select, func
from wordcloud import WordCloud, ImageColorGenerator

from library import prefix_match, config
from library.depend import Switch, Blacklist, FunctionCall, Interval
from library.image.image import DEFAULT_FONT
from library.image.oneui_mock.elements import (
    OneUIMock,
    Banner,
    Column,
    Header,
    ProgressBar,
    GeneralBox,
    HintBox,
)
from library.orm import orm
from module.chat_recorder import ChatRecord, generate_pass

channel = Channel.current()
ASSETS_DIR = Path(__file__).parent / "assets"
DATA_DIR = config.path.data / channel.module
DATA_DIR.mkdir(exist_ok=True)

FILTER_FILE = DATA_DIR / "filter.txt"
FILTER_FILE.touch(exist_ok=True)
FILTER_WORDS = FILTER_FILE.read_text().splitlines()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    UnionMatch("我的", "本群", "我的本群") @ "scope",
                    UnionMatch("年内", "月内", "日内", "今日", "本月", "本年", "年度", "月度")
                    @ "period",
                    UnionMatch("总结", "词云"),
                    ArgumentMatch("-k", "--topK", type=int, optional=True) @ "top_k",
                    RegexMatch(r"[\n\r]?", optional=True),
                    ElementMatch(Image, optional=True) @ "mask",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def wordcloud_generator(
    app: Ariadne,
    event: MessageEvent,
    scope: MatchResult,
    period: MatchResult,
    top_k: ArgResult,
    mask: ElementResult,
):
    scope = scope.result.display
    if scope == "我的":
        field = -1
        sender = event.sender
    elif scope in ("本群", "我的本群") and isinstance(event, FriendMessage):
        return await app.send_message(
            event.sender, MessageChain([Plain(text="当前聊天区域不支持本群词云")])
        )
    elif scope == "本群":
        field = event.sender.group.id
        sender = 0
    else:
        field = event.sender.group.id
        sender = event.sender

    await Interval.check_and_raise(
        module=channel.module,
        supplicant=event.sender,
        minutes=3,
        on_failure=MessageChain("冷却 {interval} 后才可再次使用"),
    )

    top_k = min(int(top_k.result), 50000) if top_k.matched else 1000
    period = period.result.display

    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain("正在生成词云，请稍候..."),
    )

    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        await GroupWordCloudGenerator.get_review(
            field=field,
            sender=sender,
            review_type=period,
            target=scope,
            mask=mask.result,
            top_k=top_k,
        ),
    )


class GroupWordCloudGenerator:
    @staticmethod
    async def filter_label(label_list: list) -> list:
        not_filter = ["草"]
        filter_list = [
            "jpg",
            "png",
            "img-",
            "{",
            "}",
            "<",
            ">",
            "url",
            "pid",
            "p0",
            "www",
            ":/",
            "qq",
        ] + FILTER_WORDS
        image_filter = "mirai:"
        result = []
        for i in label_list:
            if image_filter in i:
                continue
            if i.isdigit():
                continue
            if any(word in i for word in filter_list):
                continue
            elif i in not_filter:
                result.append(i)
            elif len(i) != 1 and i.find("nbsp") < 0:
                result.append(i)
        return result

    @staticmethod
    def draw_word_cloud(read_name, mask: Optional[PillowImage.Image]) -> bytes:
        mask = np.array(
            mask
            or PillowImage.open(
                random.choice(
                    [
                        file
                        for file in ASSETS_DIR.iterdir()
                        if file.suffix in (".png", ".jpg", ".jpeg")
                    ]
                )
            )
        )
        wc = WordCloud(
            font_path=str(Path() / "library" / "assets" / "fonts" / DEFAULT_FONT),
            background_color="white",
            max_font_size=100,
            width=1920,
            height=1080,
            mask=mask,
        )
        name = []
        value = []
        for t in read_name:
            name.append(t[0])
            value.append(t[1])
        for i in range(len(name)):
            name[i] = str(name[i])
        dic = dict(zip(name, value))
        wc.generate_from_frequencies(dic)
        image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
        wc.recolor(color_func=image_colors)
        plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
        plt.axis("off")
        bytes_io = BytesIO()
        img = wc.to_image()
        img.save(bytes_io, format="PNG")
        return bytes_io.getvalue()

    @staticmethod
    async def get_review(
        field: int,
        sender: Member | Friend | int,
        review_type: str,
        target: str,
        mask: Optional[Image],
        top_k: int,
    ) -> MessageChain:
        start_time = datetime.now()
        time = datetime.now()
        time_right = time.strftime("%Y-%m-%d %H:%M:%S")
        if review_type in {"年内", "今年", "年度"}:
            timep = time - relativedelta(years=1)
            time_left = (time - relativedelta(years=1)).strftime("%Y-%m-%d %H:%M:%S")
        elif review_type in {"月内", "本月", "月度"}:
            timep = time - relativedelta(months=1)
            time_left = (time - relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            timep = time - relativedelta(days=1)
            time_left = (time - relativedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"词云 [{int(sender)}]: 正在获取发言记录")
        sql = (
            select(
                ChatRecord.seg,
            )
            .where(
                (ChatRecord.field == generate_pass(field)) if target != "我的" else True,
                (ChatRecord.sender == generate_pass(int(sender)))
                if target != "本群"
                else True,
                ChatRecord.time < time,
                ChatRecord.time > timep,
            )
            .order_by(ChatRecord.time.desc())
            .limit(5000)
        )

        if not (res := list(await orm.fetchall(sql))):
            return MessageChain("暂无发言记录")
        texts = []
        cutoff = len(res) >= 5000
        logger.info(f"词云 [{int(sender)}]: {len(res)} 条记录")
        for i in res:
            if i[0]:
                texts += await GroupWordCloudGenerator.filter_label(i[0].split("|"))
        logger.success(f"词云 [{int(sender)}]: 完成分词，共 {len(texts)} 个词")

        sql = (
            select([func.count()])
            .select_from(ChatRecord)
            .where(
                (ChatRecord.field == generate_pass(field)) if target != "我的" else True,
                (ChatRecord.sender == generate_pass(int(sender)))
                if target != "本群"
                else True,
                ChatRecord.time < time,
                ChatRecord.time > timep,
            )
        )
        if not (res := list(await orm.fetchone(sql))):
            return MessageChain("暂无发言记录")
        times = res[0]

        sql = (
            select([func.count()])
            .select_from(ChatRecord)
            .where(
                True
                if field == -1 or int(sender) == 0
                else (ChatRecord.field == generate_pass(field)),
                ChatRecord.time < time,
                ChatRecord.time > timep,
            )
        )
        global_times = list(await orm.fetchone(sql))[0] or times

        if mask:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=mask.url) as resp:
                    mask = PillowImage.open(BytesIO(await resp.read()))
        loop = asyncio.get_event_loop()

        logger.info(f"词云 [{int(sender)}]: 开始绘制词云")
        column = Column(
            Banner("词云", icon=PillowImage.open(Path(__file__).parent / "icon.png")),
        )
        if target != "本群":
            avatar = await sender.get_avatar()
            _scope = "全局" if target == "我的" else "本群"
            column.add(
                Header(
                    f"[{sender.name if isinstance(sender, Member) else sender.nickname}]",
                    f"{_scope}词云",
                    icon=PillowImage.open(BytesIO(avatar)),
                )
            )
        column.add(
            PillowImage.open(
                BytesIO(
                    await loop.run_in_executor(
                        None,
                        GroupWordCloudGenerator.draw_word_cloud,
                        jieba.analyse.extract_tags(
                            " ".join(texts), topK=top_k, withWeight=True, allowPOS=()
                        ),
                        mask,
                    )
                )
            )
        ).add(GeneralBox("记录时间", f"{time_left} ~ {time_right}")).add(
            ProgressBar(
                (ratio := times / global_times) * 100,
                f"所占{'本群' if target == '我的' else '全局'}比例",
                f"{ratio:.2%}",
            )
        ).add(
            GeneralBox("发言次数", f"{times} 次").add(
                f"{'本群' if target == '我的' else '全局'}发言总数", f"{global_times} 次"
            )
        )
        if cutoff:
            column.add(HintBox("提示", "由于数据量过大，只显示了最新的 5000 条记录"))

        logger.success(f"词云 [{int(sender)}]: 完成绘制词云，等待 Playwright 渲染")
        logger.success(f"词云 [{int(sender)}]: 耗时 {datetime.now() - start_time}")
        return MessageChain(
            Image(data_bytes=await OneUIMock(column).async_render_bytes())
        )
