import asyncio
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Tuple

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    WildcardMatch,
    MatchResult,
    RegexMatch,
)
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl, Waiter
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Switch, Permission, FunctionCall
from library.model import UserPerm

saya = Saya.current()
channel = Channel.current()

channel.name("ShellExecutor")
channel.author("nullqwertyuiop")
channel.description("")

data_dir = Path(config.path.data) / channel.module
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
            FunctionCall.record(channel.module),
        ],
    )
)
async def execute_shell(ariadne: Ariadne, event: GroupMessage, command: MatchResult):
    command = command.result.display.strip()

    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def confirmation_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if (
            waiter_group.id == event.sender.group.id
            and waiter_member.id == event.sender.id
        ):
            return waiter_message.display == "是"

    await ariadne.send_group_message(
        event.sender.group, MessageChain("请确认是否执行以下 Shell (是/否)\n" f"{command}")
    )
    try:
        if not await asyncio.wait_for(
            InterruptControl(ariadne.broadcast).wait(confirmation_waiter), 30
        ):
            return await ariadne.send_group_message(
                event.sender.group, MessageChain("已取消本次执行")
            )
    except asyncio.TimeoutError:
        return await ariadne.send_group_message(
            event.sender.group, MessageChain("超时，已取消本次执行")
        )
    with Path(data_dir, "history.txt").open("a+", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\t"
            f"{event.sender.id}\t{command}\n"
        )
    stdout, stderr = await async_execute(command)
    msg = f"stdout: \n{stdout}"
    if stderr:
        msg += f"\n==========\nstderr: \n{stderr}"
    await ariadne.send_group_message(
        event.sender.group,
        MessageChain(msg),
    )


def execute(command: str) -> Tuple[str, str]:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    return stdout.decode("utf-8"), stderr.decode("utf-8")


async def async_execute(command: str) -> Tuple[str, str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, execute, command)
