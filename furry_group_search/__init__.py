import asyncio
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO

import qrcode
from aiohttp import ClientSession
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Forward, ForwardNode
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ParamMatch,
    RegexResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from pydantic import BaseModel, root_validator

from library import config, prefix_match
from library.depend import Switch, FunctionCall, Blacklist

saya = Saya.current()
channel = Channel.current()

channel.name("FurryGroupSearch")
channel.author("nullqwertyuiop")
channel.description("")


class CityGroupLoc(BaseModel):
    id: int
    province: str
    city: str | None


class CityGroup(BaseModel):
    location: CityGroupLoc
    group: int
    level: int
    name: str
    url: str | None
    valid: int

    @root_validator(pre=True, allow_reuse=True)
    def furry_group_search_validator(cls, values: dict):
        if "valid" not in values:
            values["valid"] = values.get("vaild")
        return values


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(prefix_match(), FullMatch("同城群"), ParamMatch() @ "city")
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def furry_group_search(app: Ariadne, event: MessageEvent, city: RegexResult):
    city = city.result.display
    async with ClientSession() as session:
        async with session.get(
            f"https://api.fursuitguide.yooofur.com:26364/cityGroup/"
            f"search?type=3&keyword={urllib.parse.quote(city)}"
        ) as resp:
            data = await resp.json()
    if data.get("code", 0) != 100:
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(
                [
                    Plain(f"无法找到 {city} 的同城群\n"),
                    Plain("==========\n"),
                    Plain("可扫码提交收录同城群信息"),
                    Image(
                        data_bytes=await async_generate_qr(
                            "https://docs.qq.com/form/page/DQWVod0VFa1VsQkFL?_w_tencentdocx_form=1"
                        )
                    ),
                ]
            ),
        )
    msg = await generate_forward(data.get("data"))
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender, msg
    )


async def generate_forward(full_data: list) -> MessageChain:
    order = ["市级群", "省级群", "省内其他市级"]
    offset = 0
    nodes = []
    for index, data in enumerate(full_data):
        if not data:
            continue
        nodes.append(
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now() + timedelta(seconds=5 * offset),
                message=MessageChain(f"====={order[index]}====="),
            )
        )
        offset += 1
        groups = [CityGroup(**item) for item in data]
        for group_index, group in enumerate(groups):
            nodes.append(
                ForwardNode(
                    target=config.account,
                    name=f"{config.name}#{config.num}",
                    time=datetime.now() + timedelta(seconds=5 * offset),
                    message=MessageChain(
                        [
                            Plain(f"{group_index + 1}. {group.name}\n"),
                            Plain(
                                f"地区：{group.location.province}{group.location.city or ''}\n"
                            ),
                            Plain(f"群号：{group.group}\n")
                            if group.valid
                            else Plain(f"进入该群需先添加：{group.group}"),
                            Image(data_bytes=await async_generate_qr(group.url))
                            if group.valid
                            else Plain(""),
                        ]
                    ),
                )
            )
            offset += 1
    nodes.append(
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now() + timedelta(seconds=5 * offset),
            message=MessageChain(
                [
                    Plain("==========\n"),
                    Plain("可扫码提交收录同城群信息\n"),
                    Image(
                        data_bytes=await async_generate_qr(
                            "https://docs.qq.com/form/page/DQWVod0VFa1VsQkFL?_w_tencentdocx_form=1"
                        )
                    ),
                ]
            ),
        )
    )
    return MessageChain([Forward(nodes)])


def generate_qr(content: str):
    qr = qrcode.QRCode(border=0)
    qr.add_data(content)
    qr.make(fit=True)
    output = BytesIO()
    qr.make_image(fill_color=(0, 0, 0)).save(output)
    return output.getvalue()


async def async_generate_qr(content: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_qr, content)
