import asyncio
from datetime import datetime

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, At, Image, Forward, ForwardNode
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, SpacePolicy
from graia.ariadne.message.parser.twilight import (
    UnionMatch,
    RegexMatch,
    ElementMatch,
    ElementResult,
)
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from library import config
from library.depend import Switch, FunctionCall
from module.image_searcher.engines import (
    __engines__,
    custom_cfg_keys,
)

saya = Saya.current()
channel = Channel.current()

channel.name("ImageSearcher")
channel.author("nullqwertyuiop")
channel.description("")

if not (__cfg := config.get_module_config(channel.module)):
    config.update_module_config(
        channel.module,
        {
            engine: {"switch": True, **{key: None for key in keys}}
            for engine, keys in custom_cfg_keys
        },
    )
else:
    for __engine, __keys in custom_cfg_keys.items():
        __keys.append("switch")
        if not __cfg.get(__engine, None):
            __cfg.update(
                {
                    __engine: {
                        "switch": True,
                        **{key: None for key in custom_cfg_keys[__engine]},
                    }
                }
            )
            continue
        for __key in __keys:
            if not __cfg.get(__engine, {}).get(__key, None):
                __cfg[__engine].update(
                    {__key: None} if __key != "switch" else {"switch": True}
                )
    config.update_module_config(channel.module, __cfg)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                    UnionMatch("搜图", "识图", "以图搜图"),
                    RegexMatch(r"[\s]+", optional=True),
                    ElementMatch(Image, optional=True) @ "image",
                ]
            )
        ],
        decorators=[Switch.check(channel.module), FunctionCall.record(channel.module)],
    )
)
async def image_searcher(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    image: ElementResult,
):
    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def image_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            if waiter_message.has(Image):
                return waiter_message.get_first(Image).url
            else:
                return False

    if not image.matched:
        try:
            await app.send_group_message(
                group, MessageChain("请在30s内发送要处理的图片"), quote=message.get_first(Source)
            )
            image = await asyncio.wait_for(
                InterruptControl(app.broadcast).wait(image_waiter), 30
            )
            if not image:
                return await app.send_group_message(
                    group,
                    MessageChain("未检测到图片，请重新发送，进程退出"),
                    quote=message.get_first(Source),
                )
        except asyncio.TimeoutError:
            return await app.send_group_message(
                group, MessageChain("图片等待超时，进程退出"), quote=message.get_first(Source)
            )
    else:
        image = image.result.url
    await app.send_group_message(
        group, MessageChain("已收到图片，正在进行搜索..."), quote=message.get_first(Source)
    )
    tasks = [
        asyncio.create_task(engine(proxies=config.proxy, url=image))
        for name, engine in __engines__.items()
        if config.get_module_config(channel.module, name).get("switch", False)
    ]
    msgs = await asyncio.gather(*tasks)
    await app.send_group_message(
        group,
        MessageChain(
            [
                Forward(
                    [
                        ForwardNode(
                            target=config.account,
                            time=datetime.now(),
                            name=f"{config.name}#{config.num}",
                            message=msg,
                        )
                        for msg in msgs
                    ]
                )
            ]
        ),
    )
