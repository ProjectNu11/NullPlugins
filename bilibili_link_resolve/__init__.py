import json
import re
import time
from typing import Union

import aiohttp
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, WildcardMatch
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from library.depend import Switch

saya = Saya.current()
channel = Channel.current()

channel.name("BilibiliLinkResolve")
channel.author("nullqwertyuiop")
channel.description("B站链接解析")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    WildcardMatch(),
                    RegexMatch(
                        r"(http:|https:\/\/)?([^.]+\.)?"
                        r"(bilibili\.com\/video\/"
                        r"((BV|bv)[\w\d]{10}|"
                        r"((AV|av)([\d]+))))|"
                        r"(b23\.tv\/[\w\d]+)"
                    ).flags(re.S),
                    WildcardMatch(),
                ]
            )
        ],
        decorators=[Switch.check(channel.module)],
    )
)
async def bilibili_link_resolve_handler(app: Ariadne, event: MessageEvent):
    await app.sendMessage(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        await BilibiliLinkResolve.resolve(event.messageChain.asDisplay()),
    )


class BilibiliLinkResolve:
    @classmethod
    async def resolve(cls, message: str) -> Union[None, MessageChain]:
        if match := re.findall(
            r"(?:http:|https://)?(?:[^.]+\.)?bilibili\.com/video/(?:BV|bv)([\w\d]{10})",
            message,
        ):
            bv = "bv" + match[0]
            av = cls.bv_to_av(bv)
            info = await BilibiliLinkResolve.get_info(av)
            return await cls.generate_messagechain(info)
        elif match := re.findall(
            r"(?:http:|https://)?(?:[^.]+\.)?bilibili\.com/video/(?:AV|av)(\d+)",
            message,
        ):
            av = match[0]
            info = await cls.get_info(av)
            return await cls.generate_messagechain(info)
        elif match := re.findall(
            r"(http:|https:/\)?(?:[^.]+\.)?b23\.tv/[\w\d]+)", message
        ):
            match = match[0]
            if not (match.startswith("http")):
                match = "https://" + match
            async with get_running(Adapter).session.get(match) as res:
                if res.status == 200:
                    link = str(res.url)
                    return await cls.resolve(link)

    @staticmethod
    async def get_info(av: int):
        bilibili_video_api_url = (
            f"https://api.bilibili.com/x/web-interface/view?aid={av}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url=bilibili_video_api_url) as resp:
                result = (await resp.read()).decode("utf-8")
        result = json.loads(result)
        return result

    @staticmethod
    def bv_to_av(bv: str) -> int:
        table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
        tr = {}
        for i in range(58):
            tr[table[i]] = i
        s = [11, 10, 3, 8, 4, 6]
        xor = 177451812
        add = 8728348608
        r = 0
        for i in range(6):
            r += tr[bv[s[i]]] * 58**i
        return (r - add) ^ xor

    @staticmethod
    def av_to_bv(av: int) -> str:
        table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
        tr = {}
        for i in range(58):
            tr[table[i]] = i
        s = [11, 10, 3, 8, 4, 6]
        xor = 177451812
        add = 8728348608
        av = (av ^ xor) + add
        r = list("BV1  4 1 7  ")
        for i in range(6):
            r[s[i]] = table[av // 58**i % 58]
        return "".join(r)

    @classmethod
    async def generate_messagechain(cls, info: dict) -> MessageChain:
        config = "%封面%\n【标题】%标题%\n【UP主】%up%\n【播放量】%播放量%\n【点赞量】%点赞量%\n【简介】%简介%"
        data = info["data"]
        chain_list = []

        async def replace_variable(text: str) -> str:
            try:
                description = str(data["desc"]).replace("\\n", "\n")
                if len(description) >= 200:
                    description = description[:200] + "..."
                text = text.replace("%标题%", str(data["title"]))
                text = text.replace(
                    "%分区%",
                    str(data["tid"]),
                )
                text = text.replace("%视频类型%", "原创" if data["copyright"] == 1 else "转载")
                text = text.replace(
                    "%投稿时间%",
                    str(
                        time.strftime("%Y-%m-%d", time.localtime(int(data["pubdate"])))
                    ),
                )
                text = text.replace("%视频长度%", str(cls.sec_format(data["duration"])))
                text = text.replace("%up%", str(data["owner"].get("name", "")))
                text = text.replace("%播放量%", str(data["stat"].get("view", "")))
                text = text.replace("%弹幕量%", str(data["stat"].get("danmaku", "")))
                text = text.replace("%评论量%", str(data["stat"].get("reply", "")))
                text = text.replace("%点赞量%", str(data["stat"].get("like", "")))
                text = text.replace("%投币量%", str(data["stat"].get("coin", "")))
                text = text.replace("%收藏量%", str(data["stat"].get("favorite", "")))
                text = text.replace("%转发量%", str(data["stat"].get("share", "")))
                text = text.replace("%简介%", description)
                text = text.replace("%av号%", "av" + str(data["aid"]))
                text = text.replace("%bv号%", str(data["bvid"]))
                text = text.replace(
                    "%链接%", f"https://www.bilibili.com/video/av{str(data['aid'])}"
                )
            except Exception as e:
                logger.error(e)
            return text

        try:
            if "%封面%" in config:
                first = True if config.startswith("%封面%") else False
                parsed_config = config.split("%封面%")
                img_url = data["pic"]
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=img_url) as resp:
                        img_content = await resp.read()
                cover = Image(data_bytes=img_content)
                chain_list.append(cover if first else None)
                for item in parsed_config[1:]:
                    chain_list.append(Plain(text=await replace_variable(item)))
            else:
                chain_list = [Plain(text=await replace_variable(config))]
        except Exception as e:
            return MessageChain(f"解析失败，请联系机器人管理员。\n{e}")
        return MessageChain.create(chain_list)

    @staticmethod
    def sec_format(secs: int) -> str:
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return "%2d:%2d:%2d" % (h, m, s)
