import asyncio
import re
from pathlib import Path
from typing import Tuple

import pyzipper
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    RegexMatch,
)
from graia.ariadne.model import UploadMethod
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from pydantic import BaseModel

from library.config import config, get_module_config, update_module_config
from library.depend import Switch, FunctionCall

saya = Saya.current()
channel = Channel.current()

data_dir = config.path.data / channel.module
data_dir.mkdir(exist_ok=True)

channel.name("EhentaiDownloader")
channel.author("nullqwertyuiop")
channel.description("")


class EHentaiCookie(BaseModel):
    ipb_member_id: str = ""
    ipb_pass_hash: str = ""
    igneous: str = ""
    extract_password: str = "project-null"
    caching: bool = True

    @classmethod
    def get_cookie_dict(cls):
        return cls(**get_module_config(channel.module)).dict()


if get_module_config(channel.module):
    update_module_config(
        channel.module, EHentaiCookie(**get_module_config(channel.module))
    )
else:
    update_module_config(
        channel.module,
        EHentaiCookie(),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(".eh"),
                    RegexMatch(r"(https?://)?e[-x]hentai\.org/g/\d+/[\da-z]+/?")
                    @ "url",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def ehentai_downloader(app: Ariadne, event: GroupMessage, url: RegexResult):
    url = url.result.asDisplay()
    gallery = re.findall(r"(?:https?://)?e[-x]hentai\.org/g/(\d+)/[\da-z]+/?", url)[0]
    try:
        async with ClientSession(cookies=EHentaiCookie.get_cookie_dict()) as session:
            async with session.get(url=url, proxy=config.proxy) as resp:
                url, name = get_archiver_and_title(
                    BeautifulSoup(await resp.text(), "html.parser")
                )
                await app.sendGroupMessage(
                    event.sender.group,
                    MessageChain(f"已取得图库 [{gallery}] {name}，正在尝试下载..."),
                )
            await session.get(url=url, proxy=config.proxy)
            async with session.post(
                url=url,
                data={"dltype": "res", "dlcheck": "Download Resample Archive"},
                proxy=config.proxy,
                allow_redirects=True,
            ) as resp:
                url = get_hath(BeautifulSoup(await resp.text(), "html.parser"))
            async with session.get(url=f"{url}?start=1", proxy=config.proxy) as resp:
                password = get_module_config(channel.module, "extract_password")
                loop = asyncio.get_event_loop()
                file = await loop.run_in_executor(
                    None,
                    encrypt_zip,
                    f"[{gallery}] {name}.zip",
                    await resp.read(),
                    password,
                )
                await app.uploadFile(
                    file,
                    UploadMethod.Group,
                    event.sender.group,
                    name=f"[{gallery}] {name}.zip",
                )
                await app.sendGroupMessage(
                    event.sender.group, MessageChain(f"解压密码 {password}")
                )
    except AttributeError:
        await app.sendGroupMessage(event.sender.group, MessageChain("请输入正确的链接"))
    except RemoteException:
        await app.sendGroupMessage(event.sender.group, MessageChain("安全检查失败，无法上传该文件"))


def get_archiver_and_title(soup: BeautifulSoup) -> Tuple[str, str]:
    return (
        soup.find("p", {"class": "g2 gsp"})
        .find("a")
        .get("onclick")
        .split("'")[1]
        .replace("https", "http")
    ), soup.find("title").get_text()


def get_hath(soup: BeautifulSoup) -> str:
    return (
        soup.find("p", {"id": "continue"})
        .find("a")
        .get("href")
        .replace("https", "http")
    )


def encrypt_zip(filename: str, data_bytes: bytes, password: str) -> bytes:
    with Path(data_dir / f"temp-{filename}").open("wb") as f:
        f.write(data_bytes)
    with pyzipper.AESZipFile(
        Path(data_dir / filename),
        "w",
        compression=pyzipper.ZIP_LZMA,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(password.encode())
        zf.setencryption(pyzipper.WZ_AES, nbits=128)
        zf.write(Path(data_dir / f"temp-{filename}"), filename)
        Path(data_dir / f"temp-{filename}").unlink(missing_ok=True)
    with Path(data_dir / filename).open("rb") as f:
        data = f.read()
    if not get_module_config(channel.module, "caching"):
        Path(data_dir / filename).unlink(missing_ok=True)
    return data
