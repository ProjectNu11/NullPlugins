from graia.ariadne import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage, MessageEvent, FriendMessage
from graia.ariadne.exception import UnknownTarget, AccountMuted
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    MatchResult,
    FullMatch,
    RegexMatch,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.depend import Permission, Blacklist, Switch, FunctionCall
from library.model import UserPerm
from .config import config, group_config, save_group_config, save_config, reset_config
from ..vars import chitung_prefix

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight([FullMatch(chitung_prefix), FullMatch("adminhelp")])
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            Permission.require(UserPerm.BOT_OWNER),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_admin_help_handler(
    app: Ariadne,
    event: MessageEvent,
):
    if event.sender.id not in config.adminID:
        return
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            "Bank：\n"
            f"{chitung_prefix}laundry 空格 金额：为自己增加/减少钱\n"
            f"{chitung_prefix}set 空格 QQ号 空格 钱：设置用户的钱的数量\n"
            f"{chitung_prefix}bank 空格 QQ号：查询用户的钱的数量\n\n"
            # "Broadcast:\n"
            # "/broadcast -f 或者 -g：进行好友或者群聊广播\n\n"
            # "Reset：\n"
            # "/reset 空格 ur：重置通用响应的配置文件\n"
            # "/reset 空格 ir：重置通用图库响应的配置文件\n"
            # "/reset 空格 config：重置 Config 配置文件\n\n"
            # "Blacklist：\n"
            # "/block 空格 -g 或者 -f 空格 QQ号：屏蔽该号码的群聊或者用户\n"
            # "/unblock 空格 -g 或者 -f 空格 QQ号：解除屏蔽该号码的群聊或者用户\n\n"
            # "Config：\n"
            # "/config -h：查看 config 的帮助\n"
            # "/config 空格 数字序号 空格 true/false：开关相应配置\n\n"
            "Data：\n"
            f"{chitung_prefix}num -f：查看好友数量\n"
            f"{chitung_prefix}num -g：查看群聊数量\n"
            f"{chitung_prefix}coverage：查看总覆盖人数"
        ),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(chitung_prefix),
                    UnionMatch("coverage", "num -f", "num -g") @ "func",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            Permission.require(UserPerm.BOT_OWNER),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_admin_tools_handler(
    app: Ariadne, event: MessageEvent, func: MatchResult
):
    func = func.result.display
    if func == "num -f":
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"七筒目前的好友数量是：{len(await app.get_friend_list())}"),
        )
    elif func == "num -g":
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"七筒目前的群数量是：{len(await app.get_group_list())}"),
        )
    else:
        group_list = await app.get_group_list()
        member_list = []
        for group in group_list:
            member_list.extend(await app.get_member_list(group))
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"七筒目前的覆盖人数是：{len(member_list)}"),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch(chitung_prefix), FullMatch("reset"), RegexMatch("config")]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            Permission.require(UserPerm.BOT_OWNER),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_reset_config_handler(app: Ariadne, event: MessageEvent):
    reset_config()
    save_config()
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain("已经重置 Config 配置文件。"),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(chitung_prefix),
                    UnionMatch("open", "close") @ "option",
                    UnionMatch(
                        "global",
                        "fish",
                        "casino",
                        "responder",
                        "game",
                        "lottery",
                        optional=True,
                    )
                    @ "funct",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            Permission.require(UserPerm.BOT_OWNER),
            FunctionCall.record(channel.module),
        ],
    )
)
async def chitung_group_config_handler(
    app: Ariadne, event: GroupMessage, option: MatchResult, funct: MatchResult
):
    funct_type = {
        "global": "全局消息",
        "fish": "钓鱼",
        "casino": "娱乐游戏",
        "responder": "关键词触发功能",
        "game": "所有游戏",
        "lottery": "C4和Bummer功能",
    }
    if not funct.matched:
        await app.send_group_message(
            event.sender.group,
            MessageChain(
                "群设置指示词使用错误，"
                "使用/close或者/open加上空格加上"
                "global、game、casino、responder、fish"
                "或者lottery来开关相应内容。"
            ),
        )
        return
    funct = funct.result.display
    value = option.result.display == "open"
    gc = group_config.get(event.sender.group.id)
    setattr(gc, funct.replace("global", "globalControl"), value)
    save_group_config()
    await app.send_group_message(
        event.sender.group,
        MessageChain(f"已设置{funct_type[funct]}的响应状态为{str(value).lower()}"),
    )


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def chitung_init_handler(app: Ariadne):
    await group_config.check()
    save_group_config()
    for group in config.devGroupID:
        try:
            await app.send_group_message(group, MessageChain(config.cc.onlineText))
        except (UnknownTarget, AccountMuted):
            continue
