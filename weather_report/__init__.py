import asyncio
import re
import urllib.parse
from datetime import datetime
from typing import Union, Tuple

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import (
    GroupMessage,
    FriendMessage,
    MessageEvent,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    RegexResult,
    RegexMatch,
)
from graia.ariadne.model import Friend
from graia.broadcast.interrupt import Waiter, InterruptControl
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema
from pydantic import BaseModel
from sqlalchemy import select

from library.config import config
from library.depend import Switch, FunctionCall
from library.orm import orm
from .table import WeatherSchedule

saya = Saya.current()
channel = Channel.current()

channel.name("WeatherReport")
channel.author("nullqwertyuiop")
channel.description("天气预报")

if not config.get_module_config(channel.module, "key"):
    config.update_module_config(channel.module, {"key": None})


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"\.(?!订阅).+天气")])],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def weather_report(app: Ariadne, event: MessageEvent):
    city = event.message_chain.display[1:-2].strip()
    if msg := await get_realtime_weather_msg(city):
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            msg,
        )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight([FullMatch(".订阅"), WildcardMatch() @ "city", FullMatch("天气")])
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def weather_report(ariadne: Ariadne, event: FriendMessage, city: RegexResult):
    city = city.result.display.strip()
    try:
        if city_info := await get_city(city, aiohttp.ClientSession()):

            @Waiter.create_using_function(listening_events=[FriendMessage])
            async def confirmation_waiter(
                waiter_friend: Friend, waiter_message: MessageChain
            ):
                if waiter_friend.id == event.sender.id:
                    return waiter_message.display == "是"

            await ariadne.send_friend_message(
                event.sender,
                MessageChain(f"是否要订阅 {city_info[1]} 的天气？(是/否)"),
            )
            try:
                assert await asyncio.wait_for(
                    InterruptControl(ariadne.broadcast).wait(confirmation_waiter), 30
                )
            except asyncio.TimeoutError:
                raise AssertionError

            @Waiter.create_using_function(listening_events=[FriendMessage])
            async def time_waiter(waiter_friend: Friend, waiter_message: MessageChain):
                if waiter_friend.id == event.sender.id:
                    if re.match(
                        r"([0-1]?\d|2[0-3])[：:][0-5]\d", waiter_message.display
                    ):
                        hour, minute = waiter_message.display.replace("：", ":").split(
                            ":"
                        )
                        return f"{int(hour):02d}{int(minute):02d}"
                    return

            await ariadne.send_friend_message(
                event.sender,
                MessageChain(f"请输入需要提醒的时间\n例：08:00"),
            )
            try:
                if time := await asyncio.wait_for(
                    InterruptControl(ariadne.broadcast).wait(time_waiter), 30
                ):
                    update = False
                    if same_time := await orm.fetchall(
                        select(
                            WeatherSchedule.time,
                        ).where(WeatherSchedule.supplicant == event.sender.id)
                    ):
                        if len(same_time) >= 5:
                            return await ariadne.send_friend_message(
                                event.sender,
                                MessageChain(f"你已订阅 {len(same_time)} 个城市天气，暂时无法订阅更多城市"),
                            )
                        if (time,) in same_time:
                            update = True
                else:
                    raise AssertionError
            except asyncio.TimeoutError:
                raise AssertionError
            await orm.insert_or_update(
                WeatherSchedule,
                [WeatherSchedule.supplicant == event.sender.id],
                {
                    "supplicant": event.sender.id,
                    "time": time,
                    "city": city_info[0],
                },
            )
            return await ariadne.send_friend_message(
                event.sender,
                MessageChain(
                    f"已{'更新' if update else '订阅'}"
                    f"每天 {time[:2]}:{time[-2:]} 的 "
                    f"{city_info[1]} 天气"
                ),
            )

        else:
            raise ValueError
    except ValueError:
        return await ariadne.send_friend_message(
            event.sender, MessageChain(f"无法获取 {city} 的天气")
        )
    except AssertionError:
        return await ariadne.send_friend_message(event.sender, MessageChain("已取消该操作"))


@channel.use(SchedulerSchema(timer=timers.crontabify("* * * * * 30")))
async def weather_schedule(app: Ariadne):
    if schedules := await orm.fetchall(
        select(
            WeatherSchedule.supplicant,
            WeatherSchedule.city,
        ).where(WeatherSchedule.time == datetime.now().strftime("%H%M"))
    ):
        for schedule in schedules:
            supplicant, city_code = schedule
            await app.send_friend_message(
                supplicant, MessageChain(await get_realtime_weather_msg(city_code))
            )


async def get_city(
    city_name: str, session: aiohttp.ClientSession
) -> Union[None, Tuple[str, str]]:
    async with session.get(
        url="https://geoapi.qweather.com/v2/city/lookup"
        f"?key={config.get_module_config(channel.module, 'key')}"
        f"&location={urllib.parse.quote(city_name)}"
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            if data["code"] == "200":
                return data["location"][0]["id"], data["location"][0]["name"]


class RealtimeWeather(BaseModel):
    obsTime: datetime
    temp: int
    feelsLike: int
    text: str
    wind360: int
    windDir: str
    windScale: int
    windSpeed: int
    humidity: int
    precip: float
    pressure: int
    vis: int
    cloud: Union[None, int]
    dew: Union[None, int]


async def get_realtime_weather(
    city_code: str, session: aiohttp.ClientSession
) -> Union[None, RealtimeWeather]:
    async with session.get(
        url="https://devapi.qweather.com/v7/weather/now"
        f"?key={config.get_module_config(channel.module, 'key')}"
        f"&location={urllib.parse.quote(city_code)}"
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            if data["code"] == "200":
                return RealtimeWeather(**data["now"])


async def get_realtime_weather_msg(city_name: str) -> Union[None, MessageChain]:
    msg = None
    try:
        async with aiohttp.ClientSession() as session:
            if not (city_info := await get_city(city_name, session)):
                raise ValueError
            city_code, city_name = city_info
            if realtime_weather := await get_realtime_weather(city_code, session):
                msg = MessageChain(
                    f"{city_name}的天气如下\n\n"
                    f"天气状况：{realtime_weather.text}\n"
                    f"温度：{realtime_weather.temp} °C\n"
                    f"相对湿度：{realtime_weather.humidity}%\n"
                    f"体感温度：{realtime_weather.feelsLike} °C\n"
                    f"风向：{realtime_weather.windDir}\n"
                    f"风力：{realtime_weather.windScale} 级\n"
                    f"风速：{realtime_weather.windSpeed} km/h\n"
                    f"当前小时累计降水量：{realtime_weather.precip} mm\n"
                    f"气压：{realtime_weather.pressure} 百帕\n"
                    f"能见度：{realtime_weather.vis} km\n"
                    f"观测时间：{realtime_weather.obsTime.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                raise ValueError
    except ValueError:
        msg = MessageChain(f"无法获取 {city_name} 的天气")
    finally:
        return msg
