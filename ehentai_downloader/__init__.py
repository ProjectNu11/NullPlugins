import asyncio
import re
import traceback
from pathlib import Path

import pyzipper
from aiohttp import ClientSession, ClientConnectorError, TCPConnector
from bs4 import BeautifulSoup
from graia.ariadne import Ariadne
from graia.ariadne.connection.util import UploadMethod
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    RegexMatch,
    UnionMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from pydantic import BaseModel

from library.config import config
from library.depend import Switch, FunctionCall
from library.depend.interval import Interval

saya = Saya.current()
channel = Channel.current()

data_dir = Path(config.path.data, channel.module)
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
        return cls(**config.get_module_config(channel.module)).dict(
            include={"ipb_member_id", "ipb_pass_hash", "igneous"}
        )


if config.get_module_config(channel.module):
    config.update_module_config(
        channel.module, EHentaiCookie(**config.get_module_config(channel.module))
    )
else:
    config.update_module_config(
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
                    UnionMatch(),
                    RegexMatch(r"(https?://)?e[-x]hentai\.org/g/\d+/[\da-z]+/?")
                    @ "url",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            FunctionCall.record(channel.module),
            Interval.check(
                channel.module, minutes=5, on_failure=MessageChain("欲求不满的扫购...")
            ),
        ],
    )
)
async def ehentai_downloader(ariadne: Ariadne, event: GroupMessage, url: RegexResult):
    url = url.result.display
    gallery = re.findall(r"(?:https?://)?e[-x]hentai\.org/g/(\d+)/[\da-z]+/?", url)[0]
    try:
        async with ClientSession(
            connector=TCPConnector(verify_ssl=False),
            cookies=EHentaiCookie.get_cookie_dict(),
        ) as session:
            async with session.get(url=url, proxy=config.proxy) as resp:
                url, name = get_archiver_and_title(
                    BeautifulSoup(await resp.text(), "html.parser")
                )
                name = name_validator(name)
                await ariadne.send_group_message(
                    event.sender.group,
                    MessageChain(f"已取得图库 [{gallery}] {name}，正在尝试下载..."),
                )
            await session.get(url=url, proxy=config.proxy)
            async with session.post(
                url=url,
                data={"dltype": "res", "dlcheck": "Download Resample Archive"},
                proxy=config.proxy,
                verify_ssl=False,
            ) as resp:
                url = get_hath(BeautifulSoup(await resp.text(), "html.parser"))
            async with session.get(url=f"{url}?start=1", proxy=config.proxy) as resp:
                password = config.get_module_config(channel.module, "extract_password")
                loop = asyncio.get_event_loop()
                file = await loop.run_in_executor(
                    None,
                    encrypt_zip,
                    f"[{gallery}] {name}.zip",
                    await resp.read(),
                    password,
                )
        await ariadne.send_group_message(
            event.sender.group, MessageChain(f"已取得文件 [{gallery}] {name}.zip，正在上传")
        )
        await ariadne.upload_file(
            file,
            UploadMethod.Group,
            event.sender.group,
            name=f"[{gallery}] {name}.zip",
        )
        await ariadne.send_group_message(
            event.sender.group, MessageChain(f"解压密码 {password}")
        )
    except AttributeError:
        logger.error(traceback.format_exc())
        await ariadne.send_group_message(
            event.sender.group, MessageChain("图库链接无效或 GP 不足")
        )
    except ClientConnectorError:
        logger.error(traceback.format_exc())
        await ariadne.send_group_message(event.sender.group, MessageChain("网络错误，请稍后再试"))
    except RemoteException:
        logger.error(traceback.format_exc())
        await ariadne.send_group_message(event.sender.group, MessageChain("出现远端错误"))
        raise
    except asyncio.exceptions.TimeoutError:
        await ariadne.send_group_message(event.sender.group, MessageChain("上传超时"))
        raise


def get_archiver_and_title(soup: BeautifulSoup) -> tuple[str, str]:
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
        Path(data_dir, filename),
        "w",
        compression=pyzipper.ZIP_LZMA,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(password.encode())
        zf.setencryption(pyzipper.WZ_AES)
        zf.write(Path(data_dir / f"temp-{filename}"), filename)
        Path(data_dir / f"temp-{filename}").unlink(missing_ok=True)
    with Path(data_dir, filename).open("rb") as f:
        data = f.read()
    if not config.get_module_config(channel.module, "caching"):
        Path(data_dir / filename).unlink(missing_ok=True)
    return data


def name_validator(name: str) -> str:
    return re.sub(r"[\\/:*?'\"<>|]", " ", name)
