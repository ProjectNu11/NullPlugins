import urllib.parse
from datetime import datetime
from typing import Union, Tuple

from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import (
    GroupMessage,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    RegexResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from pydantic import BaseModel

from library.config import get_module_config, update_module_config
from library.depend import Switch

saya = Saya.current()
channel = Channel.current()

channel.name("Repeater")
channel.author("nullqwertyuiop")
channel.description("人类的本质")

if not get_module_config(channel.module, "key"):
    update_module_config(channel.module, {"key": None})


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("."), WildcardMatch() @ "city", FullMatch("天气")])
        ],
        decorators=[Switch.check(channel.module)],
    )
)
async def weather_report(app: Ariadne, event: GroupMessage, city: RegexResult):
    msg = None
    city = city.result.asDisplay()
    try:
        if city_info := await get_city(city):
            city_code, city_name = city_info
            if realtime_weather := await get_realtime_weather(city_code):
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
        else:
            raise ValueError
    except ValueError:
        msg = MessageChain(f"无法获取 {city} 的天气")
    finally:
        if msg:
            await app.sendGroupMessage(
                event.sender.group,
                msg,
            )


async def get_city(city_name: str) -> Union[None, Tuple[str, str]]:
    async with get_running(Adapter).session.get(
        url="https://geoapi.qweather.com/v2/city/lookup"
        f"?key={get_module_config(channel.module, 'key')}"
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


async def get_realtime_weather(city_code: str) -> Union[None, RealtimeWeather]:
    async with get_running(Adapter).session.get(
        url="https://devapi.qweather.com/v7/weather/now"
        f"?key={get_module_config(channel.module, 'key')}"
        f"&location={urllib.parse.quote(city_code)}"
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            if data["code"] == "200":
                return RealtimeWeather(**data["now"])
