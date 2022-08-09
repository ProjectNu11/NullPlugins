import asyncio
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Tuple

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    WildcardMatch,
    MatchResult,
    RegexMatch,
)
from graia.broadcast import PropagationCancelled
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch, Permission, FunctionCall, Blacklist
from library.model import UserPerm
from module.build_image import create_image

saya = Saya.current()
channel = Channel.current()

channel.name("ShellExecutor")
channel.author("nullqwertyuiop")
channel.description("")

data_dir = Path(Path(config.path.data), channel.module)
data_dir.mkdir(exist_ok=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At),
                    RegexMatch(r"[\n\r]?", optional=True),
                    FullMatch("shell"),
                    FullMatch(">"),
                    WildcardMatch().flags(re.S) @ "command",
                ]
            )
        ],
        decorators=[
            MentionMe(),
            Permission.require(UserPerm.BOT_OWNER, MessageChain("Permission denied.")),
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def execute_shell(ariadne: Ariadne, event: GroupMessage, command: MatchResult):
    command = command.result.display.strip()
    with Path(data_dir, "history.txt").open("a+", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\t"
            f"{event.sender.id}\t{command}\n"
        )
    stdout, stderr = await async_execute(command)
    msg = f"==========\nstdout: \n==========\n{stdout}"
    if stderr:
        msg += f"\n==========\nstderr: \n==========\n{stderr}"
    await ariadne.send_group_message(
        event.sender.group,
        MessageChain([Image(data_bytes=await create_image(msg, cut=120))]),
    )
    raise PropagationCancelled


def execute(command: str) -> Tuple[str, str]:
    process = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout = process.stdout
    stderr = process.stderr
    try:
        return stdout.decode("utf-8"), stderr.decode("utf-8")
    except UnicodeDecodeError:
        return stdout.decode("gbk"), stderr.decode("gbk")


async def async_execute(command: str) -> Tuple[str, str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, execute, command)
