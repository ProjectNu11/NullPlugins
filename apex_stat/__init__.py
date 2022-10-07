import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.ariadne.message.parser.twilight import WildcardMatch, RegexResult
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import prefix_match
from library.depend import Switch, Blacklist, FunctionCall
from library.image.oneui_mock.elements import (
    Banner,
    Column,
    Header,
    OneUIMock,
    HintBox,
    GeneralBox,
)

saya = Saya.current()
channel = Channel.current()

channel.name("ApexStat")
channel.author("SAGIRI-kawaii")
channel.author("nullqwertyuiop")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    FullMatch("apex"),
                    WildcardMatch() @ "player",
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
async def apex_stat(app: Ariadne, event: MessageEvent, player: RegexResult):
    url = f"https://www.jumpmaster.xyz/user/Stats?platform=PC&player={player.result.display.strip()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    if error := data.get("error"):
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(
                Image(
                    data_bytes=await OneUIMock(
                        Column(
                            Banner("Apex 数据查询"),
                            Header("运行查询时出现错误", str(error)),
                            HintBox(
                                "可以尝试以下解决方案",
                                "检查用户名是否有效",
                                "检查是否超出查询速率限制",
                                "检查 API 是否可用",
                                "检查网络链接是否正常",
                            ),
                        )
                    ).async_render_bytes()
                )
            ),
        )
    user = data["user"]
    user_name = user.get("username", "null")
    status = user.get("status", {})
    online = bool(status.get("online"))
    in_game = bool(status.get("ingame"))
    party_in_match = bool(status.get("partyInMatch"))
    if in_game:
        match_length = status.get("matchLength")
        if match_length:
            match_length = f"{match_length // 60}分钟{match_length % 60}秒"
        current_status = f"正在游戏，游戏时长{match_length}"
    elif party_in_match:
        current_status = "正在匹配"
    elif online:
        current_status = "在线"
    else:
        current_status = "离线"
    bans = user.get("bans", {})
    bans_active = bool(bans.get("active"))
    bans_length = bans.get("length")
    bans_reason = bans.get("reason")
    if bans_active:
        if bans_length:
            bans_length = f"{bans_length // 60}分钟{bans_length % 60}秒"
        bans_status = f"封禁中\n封禁时长：{bans_length}\n封禁原因：{bans_reason}"
    else:
        bans_status = "未封禁"
    account = data["account"]
    level = account.get("level", {}).get("current")
    ranked = data["ranked"]
    br = ranked.get("BR", {})
    br_score = br.get("score")
    br_name = br.get("name").strip()
    br_division = br.get("division")
    arenas = ranked.get("Arenas", {})
    arenas_score = arenas.get("score")
    arenas_name = arenas.get("name").strip()
    arenas_division = arenas.get("division")

    column = Column(Banner("Apex 数据查询"), Header(user_name, f"{level} 级"))

    box = GeneralBox()
    box.add("当前状态", current_status)
    box.add("封禁状态", bans_status)
    column.add(box)

    box = GeneralBox()
    box.add("大逃杀分数", str(br_score))
    box.add("大逃杀段位", f"{br_name} {br_division}")
    column.add(box)

    box = GeneralBox()
    box.add("竞技场分数", str(arenas_score))
    box.add("竞技场段位", f"{arenas_name} {arenas_division}")
    column.add(box)

    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(Image(data_bytes=await OneUIMock(column).async_render_bytes())),
    )
