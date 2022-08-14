import asyncio
import math
import random
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

from graia.ariadne import Ariadne
from graia.ariadne.event.message import (
    Member,
    GroupMessage,
    FriendMessage,
    MessageEvent,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
    UnionMatch,
    FullMatch,
    RegexResult,
)
from graia.ariadne.model import Friend
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

from library.depend import Switch, FunctionCall
from library.depend.interval import Interval

from library import config
from library.depend import Switch, FunctionCall


channel = Channel.current()

assets_path = Path(Path(__file__).parent, "assets")
settings_file = Path(assets_path / "news_settings.json")

with settings_file.open("r", encoding="UTF-8") as f:
    _data = json.loads(f.read())
    ENCHANT_TEMPLATES = _data["enchant"]
    COLOR_TEMPLATES = _data["news_color"]
    OUTWARD_TEMPLATES = _data["outward"]
    EVALUATE_TEMPLATES_0 = _data["news_evaluate_0"]
    EVALUATE_TEMPLATES_1 = _data["news_evaluate_1"]
    EVALUATE_TEMPLATES_2 = _data["news_evaluate_2"]
    EVALUATE_TEMPLATES_3 = _data["news_evaluate_3"]
    EVALUATE_TEMPLATES_4 = _data["news_evaluate_4"]
    EVALUATE_TEMPLATES_5 = _data["news_evaluate_5"]
    COMMENT_TEMPLATES_0 = _data["public_comment_0"]
    COMMENT_TEMPLATES_1 = _data["public_comment_1"]
    COMMENT_TEMPLATES_2 = _data["public_comment_2"]
    COMMENT_TEMPLATES_3 = _data["public_comment_3"]
    COMMENT_TEMPLATES_4 = _data["public_comment_4"]
    COMMENT_TEMPLATES_5 = _data["public_comment_5"]
_data


@channel.use(
    ListenerSchema(
        [GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch("牛子", "牛至"),
                    UnionMatch("多长", "多長", "長度", "长度"),
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def random_dick_length(app: Ariadne, event: MessageEvent):
    RandomSeed(event.sender)
    dick_color = random.choice(COLOR_TEMPLATES)
    dick_outward = random.choice(OUTWARD_TEMPLATES)
    if random.randint(0, 4) == 0:
        dick_enchant = random.choice(ENCHANT_TEMPLATES)
    else:
        dick_enchant = ""

    if random.randint(0, 1) == 1:
        boki_status = "勃起"
        angle_status = "boki"
    else:
        boki_status = "软掉"
        angle_status = ""
        dick_color = ""
        dick_outward = ""

    angle = f"{random.randint(0, 180)}度"

    if random.randint(0, 2) == 0:
        phimosis_status = "包茎"
    elif random.randint(0, 2) == 1:
        phimosis_status = "半包茎"
    else:
        phimosis_status = "非包茎"

    dick_hardness = f"莫氏硬度为{random.randint(1, 10)}"
    egg_weight = f"{random.randint(0, 1000)}克"
    dick_legth = random.randint(-10, 30)

    if dick_legth > 20:
        dick_length_evaluate = random.choice(EVALUATE_TEMPLATES_0)
        dick_comment = random.choice(COMMENT_TEMPLATES_0)
        dick_comment_score = str(random.uniform(7, 10))
    elif dick_legth > 15 and dick_legth <= 20:
        dick_length_evaluate = random.choice(EVALUATE_TEMPLATES_1)
        dick_comment = random.choice(COMMENT_TEMPLATES_1)
        dick_comment_score = random.uniform(5, 7)
    elif dick_legth >= 10 and dick_legth <= 15:
        dick_length_evaluate = random.choice(EVALUATE_TEMPLATES_2)
        dick_comment = random.choice(COMMENT_TEMPLATES_2)
        dick_comment_score = random.uniform(3, 5)
    elif dick_legth > 0 and dick_legth < 10:
        dick_length_evaluate = random.choice(EVALUATE_TEMPLATES_3)
        dick_comment = random.choice(COMMENT_TEMPLATES_3)
        dick_comment_score = random.uniform(0, 3)
    elif dick_legth == 0:
        dick_length_evaluate = random.choice(EVALUATE_TEMPLATES_4)
        dick_comment = random.choice(COMMENT_TEMPLATES_4)
        dick_comment_score = "0"
    else:
        dick_length_evaluate = random.choice(EVALUATE_TEMPLATES_5)
        dick_comment = random.choice(COMMENT_TEMPLATES_5)
        dick_comment_score = random.uniform(3, 10)
    a = "\n"
    length_text = f"{dick_legth}cm的牛子，{a}{dick_length_evaluate}"
    dick_comment_score_1 = round(dick_comment_score, 1)

    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            f"你今天有一根{dick_enchant}{dick_color}{dick_outward}{boki_status}的，{angle_status}角度为{angle}的{phimosis_status}的{dick_hardness},并且蛋蛋{egg_weight}的{length_text}{a}大众点评：{dick_comment_score_1}分，{dick_comment}"
        ),
    )
    random.seed()


def RandomSeed(supplicant: Member | Friend):
    random.seed(int(f"{datetime.now().strftime('%Y%m%d')}{supplicant.id}"))
