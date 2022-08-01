import asyncio
import math
import random
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
    if random.randint(0, 1) == 1:
        boki_status = "勃起"
        angle_status = "boki"
    else:
        boki_status = "软掉"
        angle_status = ""
    angle = str(random.randint(0, 180)) + "度"
    if random.randint(0, 2) == 0:
        phimosis_status = "包茎"
    elif random.randint(0, 2) == 1:
        phimosis_status = "半包茎"
    else:
        phimosis_status = "非包茎"
    dick_hardness = "莫氏硬度为" + str(random.randint(1, 10))
    egg_weight = str(random.randint(0, 1000)) + "克"
    dick_legth = random.randint(-10, 30)
    if dick_legth > 20:
        dick_length_evaluate = "哪来的兽人，怎么会这么长！"
    elif dick_legth > 15 and dick_legth <= 20:
        dick_length_evaluate = "还是蛮长的"
    elif dick_legth >= 10 and dick_legth <= 15:
        dick_length_evaluate = "到了平均水准捏"
    elif dick_legth > 0 and dick_legth < 10:
        dick_length_evaluate = "好短！"
    elif dick_legth == 0:
        dick_length_evaluate = "看来你不擅长应对女人。"
    else:
        dick_length_evaluate = "dick ... 他 .. 他..他缩进去了！"
    length_text = f"{str(dick_legth)}cm的牛子，{dick_length_evaluate}"
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            f"你今天有一根{boki_status}的，{angle_status}角度为{angle}的{phimosis_status}的{dick_hardness},并且蛋蛋{egg_weight}的{length_text}"
        ),
    )
    random.seed()


def RandomSeed(supplicant: Member | Friend):
    random.seed(int(f"{datetime.now().strftime('%Y%m%d')}{supplicant.id}"))
