from typing import NoReturn

from graia.ariadne.event.message import MessageEvent, FriendMessage, GroupMessage
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from . import config
from .config import group_config


class FunctionControl:
    Fish = "fish"
    Casino = "casino"
    Responder = "responder"
    Lottery = "lottery"
    Game = "game"

    @staticmethod
    def enable(function: str) -> Depend:
        async def switch(event: MessageEvent) -> NoReturn:
            if isinstance(event, FriendMessage):
                if any([not getattr(config.friendFC, function)]):
                    raise ExecutionStop
            elif isinstance(event, GroupMessage):
                if any(
                    [
                        not getattr(config.groupFC, function),
                        not group_config.get(event.sender.group.id).globalControl,
                        not getattr(group_config.get(event.sender.group.id), function),
                    ]
                ):
                    raise ExecutionStop

        return Depend(switch)
