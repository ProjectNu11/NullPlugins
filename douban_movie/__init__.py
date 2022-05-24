import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Forward, ForwardNode, Image, Plain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    RegexResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch

saya = Saya.current()
channel = Channel.current()

channel.name("DoubanMovie")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch(".douban"), FullMatch("search"), WildcardMatch() @ "movie"]
            )
        ],
        decorators=[Switch.check(channel.module)],
    )
)
async def douban_movie_search(app: Ariadne, event: MessageEvent, movie: RegexResult):
    async with ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.67 Safari/537.36"
        }
    ) as session:
        resp = await session.get(
            f"https://www.douban.com/search?q={urllib.parse.quote(movie.result.asDisplay())}"
        )
        if resp.status != 200:
            return await app.sendMessage(
                event.sender.group if isinstance(event, GroupMessage) else event.sender,
                MessageChain(f"服务器返回错误 {resp.status}"),
            )
        if not (
            node_list := await search_movie(
                BeautifulSoup(await resp.text(), features="html.parser"), session
            )
        ):
            return await app.sendMessage(
                event.sender.group if isinstance(event, GroupMessage) else event.sender,
                MessageChain("未找到相关影片"),
            )
    await app.sendMessage(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(f"找到 {len(node_list) - 1} 条相关影片"),
    )
    await app.sendMessage(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain.create([Forward(nodeList=node_list)]),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch(".douban"), FullMatch("info"), WildcardMatch() @ "movie"]
            )
        ],
        decorators=[Switch.check(channel.module)],
    )
)
async def douban_movie_info(app: Ariadne, event: MessageEvent, movie: RegexResult):
    movie = movie.result.asDisplay()
    if not movie.isdigit():
        return await app.sendMessage(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"无效的影片 ID：{movie}"),
        )
    async with ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.67 Safari/537.36"
        }
    ) as session:
        resp = await session.get(f"https://movie.douban.com/subject/{movie}")
        if resp.status != 200:
            return await app.sendMessage(
                event.sender.group if isinstance(event, GroupMessage) else event.sender,
                MessageChain(f"服务器返回错误 {resp.status}"),
            )
        node_list = await get_movie_info(
            BeautifulSoup(await resp.text(), features="html.parser"), session
        )
        await app.sendMessage(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain.create([Forward(nodeList=node_list)]),
        )


async def search_movie(
    soup: BeautifulSoup, session: ClientSession
) -> List[ForwardNode]:
    fwd_node_list = []
    example_id = 0
    delta = 0
    for index, first_level in enumerate(
        soup.find_all("div", attrs={"class": "result"})
    ):
        if (
            not first_level.find("span", attrs={})
            or first_level.find("span", attrs={}).get_text().strip() != "[电影]"
        ):
            continue
        movie_id = re.findall(r"%2F\d+%2F", first_level.find("a").get("href"))[0].strip(
            "%2F"
        )
        cover = None
        if cover_pic := first_level.find("div", attrs={"class": "pic"}):
            async with session.get(cover_pic.find("img").get("src")) as resp:
                if resp.status == 200:
                    cover = await resp.read()
        title = (
            first_level.find("div", attrs={"class": "title"})
            .find("a")
            .get_text()
            .strip()
        )
        rating = (
            rating_info.get_text().strip()
            if (
                rating_info := (
                    first_level.find("div", attrs={"class": "title"}).find(
                        "span", attrs={"class": "rating_nums"}
                    )
                )
            )
            else "暂无数据"
        )
        cast = (
            cast_info.get_text().strip()
            if (cast_info := first_level.find("span", attrs={"class": "subject-cast"}))
            else "暂无数据"
        )
        digest = (
            digest_info.get_text() if (digest_info := first_level.find("p")) else "暂无数据"
        )
        fwd_node_list.append(
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now() + timedelta(seconds=15) * (index + 1),
                message=MessageChain.create(
                    [
                        Image(data_bytes=cover) if cover else None,
                        Plain(text=f"影名：{title}\n"),
                        Plain(text=f"编号：{movie_id}\n"),
                        Plain(text=f"评分：{rating}\n"),
                        Plain(text=f"剧组：{cast}\n"),
                        Plain(text=f"简介：{digest}"),
                    ]
                ),
            )
        )
        example_id = movie_id
        delta = index
    if fwd_node_list:
        fwd_node_list.append(
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now() + timedelta(seconds=15) * (delta + 1),
                message=MessageChain(
                    '如需查看电影详细信息，请发送 ".douban info 编号"\n'
                    f'如 ".douban info {example_id}"'
                ),
            )
        )
    return fwd_node_list


async def get_movie_info(
    soup: BeautifulSoup, session: ClientSession
) -> List[ForwardNode]:
    title = (
        soup.find("div", attrs={"id": "content"})
        .find("h1")
        .get_text()
        .replace("\n", " ")
        .strip()
    )
    info = soup.find("div", attrs={"id": "info"}).get_text().strip()

    rating_num = (
        soup.find("strong", attrs={"class": "ll rating_num"}).get_text().strip()
    )
    rating_sum = soup.find("div", attrs={"class": "rating_sum"}).get_text().strip()
    ratings_on_weight = (
        soup.find("div", attrs={"class": "ratings-on-weight"})
        .get_text()
        .replace("\n", "")
        .replace(" ", "")
        .replace("星", "星：")
        .replace("%", "%\n")
        .strip()
    )
    rating_better_than = (
        (rbt.get_text().strip().replace("  ", ""))
        if (rbt := soup.find("div", attrs={"class": "rating_betterthan"}))
        else "暂无对比数据"
    )
    rating = (
        f"评分：{rating_num} - {rating_sum}\n\n"
        f"{ratings_on_weight}\n\n"
        f"{rating_better_than}"
    )

    digest = (
        soup.find("span", attrs={"property": "v:summary"})
        .get_text()
        .replace("  ", "")
        .strip("\n")
        .strip(" ")
    )

    cover = None
    async with session.get(
        soup.find("div", attrs={"id": "mainpic"}).find("img").get("src")
    ) as resp:
        if resp.status == 200:
            cover = await resp.read()
    return (
        [
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now(),
                message=MessageChain.create([Image(data_bytes=cover)]),
            )
        ]
        if cover
        else []
    ) + [
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now() + timedelta(seconds=15),
            message=MessageChain.create(
                [
                    Plain(text=title),
                    Plain(text="\n\n"),
                    Plain(text=info),
                ]
            ),
        ),
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now() + timedelta(seconds=30),
            message=MessageChain.create(
                [
                    Plain(text=rating),
                ]
            ),
        ),
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now() + timedelta(seconds=45),
            message=MessageChain.create(
                [
                    Plain(text=digest),
                ]
            ),
        ),
    ]
