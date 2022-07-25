import asyncio
import math
import random
from datetime import datetime
from io import BytesIO
from pathlib import Path

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexMatch,
    UnionMatch,

)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

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
        decorators=[Switch.check(channel.module),
                    FunctionCall.record(channel.module)],
    )
)
async def random_dick_length(app: Ariadne, event: MessageEvent):
    await app.send_message(
        event.sender.group if isinstance(
            event, GroupMessage) else event.sender,
        MessageChain(f"你今天有一根{get_if_boki_status()}的,{get_angle_status()}角度为{get_angle()}的{get_if_phimosis_status()}的{get_dick_hardness()},并且蛋蛋{get_egg_weight()}的{dick_length()}"),
     )

def get_if_boki_status():
    boki = random.randint(0,1)
    if boki == 0:
        boki_status = "勃起"
    else:
        boki_status = "软掉"
    return boki_status

def get_angle_status():
    boki_status=get_if_boki_status()
    if boki_status == "勃起":
        angle_status = "boki"
    else:
        angle_status = ""
    return angle_status
    
def get_angle():
    angle = str(random.randint(0,180))+"度"
    return angle

def get_if_phimosis_status():
    phimosis = random.randint(0,2)
    if phimosis == 0:
        phimosis_status = "包茎"
    elif phimosis == 1:
        phimosis_status = "半包茎"
    else:
        phimosis_status = "非包茎"
    return phimosis_status

def get_dick_hardness():
    hardness = random.randint(0,10)
    dick_hardness = "莫氏硬度为" + str(hardness)
    return dick_hardness

def get_egg_weight():
    egg_weight = str(random.randint(0,10000)) + "克"
    return egg_weight

def dick_length():
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
    return length_text
