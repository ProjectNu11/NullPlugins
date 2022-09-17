import asyncio

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, MessageEvent, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import PrefixMatch
from library.depend import Switch, Blacklist, FunctionCall
from library.image.oneui_mock.elements import (
    Banner,
    Column,
    GeneralBox,
    HintBox,
    OneUIMock,
)

channel = Channel.current()

channel.name("AbbreviatedPrediction")
channel.author("SAGIRI-kawaii")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
                    FullMatch("缩"),
                    RegexMatch(r"[A-Za-z0-9 ]+").help("要缩写的内容") @ "content",
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
async def abbreviated_prediction(
    app: Ariadne, event: MessageEvent, content: RegexResult
):
    url = "https://lab.magiconch.com/api/nbnhhsh/guess"
    headers = {"referer": "https://lab.magiconch.com/nbnhhsh/"}
    data = {"text": content.result.display}

    async with Ariadne.service.client_session.post(
        url=url, headers=headers, data=data
    ) as resp:
        res = await resp.json()

    loop = asyncio.get_event_loop()

    try:
        data: dict[str, list[str]] = {}
        has_result = False
        for i in res:
            if "trans" in i and i["trans"]:
                has_result = True
                data[i["name"]] = i["trans"]
            elif "trans" in i or not i["inputting"]:
                data[i["name"]] = ["没有查询到结果"]
            else:
                has_result = True
                data[i["name"]] = i["inputting"]
        assert has_result, "没有查询到结果"

        def _compose() -> bytes:
            column = Column(Banner("缩写预测"))

            for key, value in data.items():
                column.add(GeneralBox(key, "\n".join(value)))

            return OneUIMock(column).render_bytes()

        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=await loop.run_in_executor(None, _compose))),
        )
    except AssertionError as err:
        err_text = err.args[0]

        def _compose() -> bytes:
            return OneUIMock(
                Column(
                    Banner("缩写预测"),
                    GeneralBox("运行时出现错误", err_text),
                    HintBox(
                        "可以尝试以下解决方案",
                        "检查缩写是否存在",
                        "检查缩写对应原文是否被录入",
                        "检查网络连接是否正常",
                        "检查输入内容是否在屏蔽词内",
                        "检查是否超过查询速率限制",
                        "检查 API 是否有效",
                    ),
                )
            ).render_bytes()

        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=await loop.run_in_executor(None, _compose))),
        )
